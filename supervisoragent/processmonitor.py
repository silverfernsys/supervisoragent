#!/usr/bin/env python
import httplib
import json
import logging
import os
import socket
import time
import threading
import websocket
import xmlrpclib
import sys
from supervisorprocess import SupervisorProcess


class UnixStreamHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.host)
        except socket.error as e:
            sys.exit('Supervisor not running.')


class UnixStreamTransport(xmlrpclib.Transport, object):
    def __init__(self, socket_path):
        self.socket_path = socket_path
        super(UnixStreamTransport, self).__init__()

    def make_connection(self, host):
        return UnixStreamHTTPConnection(self.socket_path)


xmlrpc = xmlrpclib.Server('http://arg_unused', transport=UnixStreamTransport('/var/run/supervisor.sock'))


def stopProcesses(args):
    ret_val = []
    if len(args) == 1 and '*' in args:
        try:
            xmlrpc.supervisor.stopAllProcesses()
            ret_val.append({'result': 'success', 'cmd': 'stop', 'process': '*', 'details': 'Stopped all processes'})
        except Exception as e:
            print('Exception stopping all processes')
            ret_val.append({'result': 'error', 'cmd': 'stop', 'process': '*', 'details': str(e)})
    else:
        for arg in args:
            try:
                xmlrpc.supervisor.stopProcess(arg)
                ret_val.append({'result': 'success', 'cmd': 'stop', 'process': arg, 'details': 'Stopped process {0}'.format(arg)})
            except Exception as e:
                print('Exception stopping process %s: %s' % (arg, e))
                ret_val.append({'result': 'error', 'cmd': 'stop', 'process': arg, 'details': str(e)})
    return ret_val


def startProcesses(args):
    ret_val = []
    if len(args) == 1 and '*' in args:
        try:
            xmlrpc.supervisor.startAllProcesses()
            ret_val.append({'result': 'success', 'cmd': 'start', 'process': '*', 'details': 'Started all processes'})
        except Exception as e:
            print('Exception starting all processes')
            ret_val.append({'result': 'error', 'cmd': 'start', 'process': '*', 'details': str(e)})
    else:
        for arg in args:
            try:
                xmlrpc.supervisor.startProcess(arg)
                ret_val.append({'result': 'success', 'cmd': 'start', 'process': arg, 'details': 'Started process {0}'.format(arg)})
            except Exception as e:
                print('Exception starting process %s: %s' % (arg, e))
                ret_val.append({'result': 'error', 'cmd': 'start', 'process': arg, 'details': str(e)})
    return ret_val


def restartProcesses(args):
    return stopProcesses(args).extend(startProcesses(args))


class WebSocketHandler(object):
    PushInterval = 0
    PushThread = None
    IsConnected = False
    Connection = None

    @classmethod
    def on_message(cls, ws, message):
        """This is where you receive messages to
        start, stop, and restart supervisor processes.
        message = {'cmd': 'start *'}
        message = {'cmd': 'stop celery'}
        message = {'cmd': 'restart web'}
        """
        msg = json.loads(message)
        if 'cmd' in msg:
            cmd = msg['cmd'].split(' ')[0]
            args = msg['cmd'].split(' ')[1:]

            if cmd == 'start':
                ret_val = startProcesses(args)
            elif cmd == 'stop':
                ret_val = stopProcesses(args)
            elif cmd == 'restart':
                ret_val = restartProcesses(args)

    @classmethod
    def on_error(cls, ws, error):
        print error

    @classmethod
    def on_close(cls, ws):
        WebSocketHandler.IsConnected = False
        WebSocketHandler.Connection = None
        print "### closed ###"

    @classmethod
    def on_open(cls, ws):
        WebSocketHandler.IsConnected = True
        WebSocketHandler.Connection = ws
        ws.send(json.dumps(SupervisorProcess.system_stats()))
        def push_stats(*args):
            while WebSocketHandler.IsConnected:
                print('SNAPSHOT_UPDATE: %s' % SupervisorProcess.snapshot_update())
                ws.send(json.dumps(SupervisorProcess.snapshot_update()))
                SupervisorProcess.reset_all()
                time.sleep(WebSocketHandler.PushInterval)

        WebSocketHandler.PushThread = threading.Thread(target=push_stats)
        WebSocketHandler.PushThread.start()
        print('Finished with on_open')


class ProcessMonitor():
    """
    This class pushes and pulls process update information.
    """
    version = 0.0

    def __init__(self, **kwargs):
        self.sample_interval = kwargs['sample_interval']
        self.push_interval = kwargs['push_interval']
        self.token = kwargs['token']
        self.url = kwargs['url']
        self.version = float(xmlrpc.supervisor.getVersion())

        data = xmlrpc.supervisor.getAllProcessInfo()
        print(xmlrpc.supervisor.getState())
        print(xmlrpc.system.listMethods())
        # print('data: %s' % data)
        for d in data:
            SupervisorProcess(d['group'], d['name'], d['pid'], d['state'], d['statename'], d['start'])

        update_stats_thread = threading.Thread(target=self.update_stats, args=())
        update_stats_thread.daemon = True
        update_stats_thread.start()

        push_data_thread = threading.Thread(target=self.push_data, args=([self.push_interval]))
        push_data_thread.daemon = True
        push_data_thread.start()

        event_server_thread = threading.Thread(target=self.event_server, args=())
        event_server_thread.daemon = True
        event_server_thread.start()

        self.restart_eventlistener()

    def restart_eventlistener(self):
        try:
            xmlrpc.supervisor.stopProcess('agenteventlistener')
        except:
            pass
        try:
            xmlrpc.supervisor.startProcess('agenteventlistener')
        except:
            pass

    def update_stats(self):
        while True:
            SupervisorProcess.update_all()
            time.sleep(self.sample_interval)

    def push_data(self, push_interval):
        while True:
            try:
                print('ProcessMonitor.push_data: create_connection')
                WebSocketHandler.PushInterval = push_interval
                ws = websocket.WebSocketApp('ws://%s:8099/supervisor/' % (self.url,),
                    header=["authorization: %s" % self.token],
                    on_message = WebSocketHandler.on_message,
                    on_error = WebSocketHandler.on_error,
                    on_open = WebSocketHandler.on_open,
                    on_close = WebSocketHandler.on_close)
                ws.run_forever()
            except Exception as e:
                print("Exception: %s" % e)
            time.sleep(60) # Wait 60 seconds before attemping to reconnect

    def event_server(self):
        logger = logging.getLogger('Event Server')
        # Create a UDS socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        server_address = '/run/supervisoragent.sock'

        # Make sure the socket does not already exist
        try:
            os.unlink(server_address)
        except OSError:
            if os.path.exists(server_address):
                raise

        logger.info('Starting server at %s' % server_address)
        sock.bind(server_address)

        # Listen for incoming connections
        sock.listen(1)

        while True:
            # Wait for a connection
            logger.info('Waiting for a connection...')
            connection, client_address = sock.accept()
            logger.info('Connected to client.')
            try:
                handle = connection.makefile()
                while True:
                    line = handle.readline()
                    headers = dict([ x.split(':') for x in line.split() ])
                    data = handle.read(int(headers['LENGTH']))
                    json_data = json.loads(data)
                    info = xmlrpc.supervisor.getProcessInfo(json_data['name'])
                    p = SupervisorProcess.get(json_data['group'], json_data['name'])
                    p.statename = json_data['statename']
                    if (p.statename == 'STOPPED'):
                        p.pid = None
                    else:
                        p.pid = json_data['pid']
                    p.start = info['start']
                    # We need to now send data off on the websocket!
                    # This is where push_update_thread's websocket needs to push
                    # data to the server that a process's state has changed.
                    if WebSocketHandler.IsConnected:
                        # process_data = p.data()
                        # No need for stats data for this update since this
                        # update is about the application's running state.
                        # process_data.pop('stats', None)
                        # data = {STATE_UPDATE: process_data}
                        print('STATE_UPDATE: data = %s' % p.state_update())
                        WebSocketHandler.Connection.send(json.dumps(p.state_update()))
            except Exception as e:
                print('Exception: %s' % e)
                print('Closing connection...')
                logger.info('Closing connection...')
                connection.close()
                logger.info('Connection closed.')

# 'supervisor.addProcessGroup',
# 'supervisor.clearAllProcessLogs',
# 'supervisor.clearLog',
# 'supervisor.clearProcessLog',
# 'supervisor.clearProcessLogs',
# 'supervisor.getAPIVersion',
# 'supervisor.getAllConfigInfo',
# 'supervisor.getAllProcessInfo',
# 'supervisor.getIdentification',
# 'supervisor.getPID',
# 'supervisor.getProcessInfo',
# 'supervisor.getState',
# 'supervisor.getSupervisorVersion',
# 'supervisor.getVersion',
# 'supervisor.readLog',
# 'supervisor.readMainLog',
# 'supervisor.readProcessLog',
# 'supervisor.readProcessStderrLog',
# 'supervisor.readProcessStdoutLog',
# 'supervisor.reloadConfig',
# 'supervisor.removeProcessGroup',
# 'supervisor.restart',
# 'supervisor.sendProcessStdin',
# 'supervisor.sendRemoteCommEvent',
# 'supervisor.shutdown',
# 'supervisor.startAllProcesses',
# 'supervisor.startProcess',
# 'supervisor.startProcessGroup',
# 'supervisor.stopAllProcesses',
# 'supervisor.stopProcess',
# 'supervisor.stopProcessGroup',
# 'supervisor.tailProcessLog',
# 'supervisor.tailProcessStderrLog',
# 'supervisor.tailProcessStdoutLog',
# 'system.listMethods',
# 'system.methodHelp',
# 'system.methodSignature',
# 'system.multicall'