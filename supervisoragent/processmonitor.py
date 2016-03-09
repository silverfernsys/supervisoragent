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
from procinfo import ProcInfo

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


class WebSocketHandler(object):
    PushInterval = 0
    PushThread = None
    IsConnected = False
    Connection = None

    @classmethod
    def on_message(self, ws, message):
        # This is where you get the 'Ack' and update the current
        # timestamp accordingly.
        print message

    @classmethod
    def on_error(self, ws, error):
        print error

    @classmethod
    def on_close(self, ws):
        WebSocketHandler.IsConnected = False
        print "### closed ###"

    @classmethod
    def on_open(self, ws):
        WebSocketHandler.IsConnected = True
        WebSocketHandler.Connection = ws
        def push_stats(*args):
            while WebSocketHandler.IsConnected:
                ws.send(json.dumps(ProcInfo.data_all()))
                ProcInfo.reset_all()
                # ws.send("STATS!")
                time.sleep(WebSocketHandler.PushInterval)

        WebSocketHandler.PushThread = threading.Thread(target=push_stats)
        WebSocketHandler.PushThread.daemon = True
        WebSocketHandler.PushThread.start()


class ProcessMonitor():
    """
    This class pushes and pulls process update information.
    """
    version = 0.0

    def __init__(self, **kwargs):
        self.sample_interval = kwargs['sample_interval']
        self.push_interval = kwargs['push_interval']
        self.xmlrpc = xmlrpclib.Server('http://arg_unused',
            transport=UnixStreamTransport('/var/run/supervisor.sock'))
        self.token = kwargs['token']
        self.url = kwargs['url']
        ProcessMonitor.version = float(self.xmlrpc.supervisor.getVersion())

        data = self.xmlrpc.supervisor.getAllProcessInfo()
        # print(self.xmlrpc.supervisor.getState())
        # print(self.xmlrpc.system.listMethods())
        # print('data: %s' % data)
        for d in data:
            ProcInfo(d['group'], d['name'], d['pid'], d['state'], d['statename'], d['start'])

        update_stats_thread = threading.Thread(target=self.update_stats, args=())
        update_stats_thread.daemon = True
        update_stats_thread.start()

        push_data_thread = threading.Thread(target=self.push_data, args=([self.push_interval]))
        push_data_thread.daemon = True
        push_data_thread.start()

        event_server_thread = threading.Thread(target=self.event_server, args=())
        event_server_thread.daemon = True
        event_server_thread.start()

    def update_stats(self):
        while True:
            ProcInfo.updateall()
            time.sleep(self.sample_interval)

    def push_data(self, push_interval):
        while True:
            try:
                print('ProcessMonitor.push_data: create_connection')
                WebSocketHandler.PushInterval = push_interval
                ws = websocket.WebSocketApp('ws://%s:8081/agent/' % (self.url,),
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
                    p = ProcInfo.get(json_data['group'], json_data['name'])
                    p.statename = json_data['statename']
                    if (p.statename == 'STOPPED'):
                        p.pid = None
                    else:
                        p.pid = json_data['pid']
                    # We need to now send data off on the websocket!
                    # This is where push_update_thread's websocket needs to push
                    # data to the server that a process's state has changed.
                    if WebSocketHandler.IsConnected:
                        data = p.data()
                        # No need for cpu or mem data for this update since this
                        # update is about the application's running state.
                        data.pop('cpu', None)
                        data.pop('mem', None)
                        WebSocketHandler.Connection.send(json.dumps([data]))
            except Exception as e:
                print('Exception: %s' % e)
                print('Closing connection...')
                logger.info('Closing connection...')
                connection.close()
                logger.info('Connection closed.')
