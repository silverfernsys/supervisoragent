#!/usr/bin/env python
import json
import time
from threading import Thread
from urlparse import urlparse
from websocket import WebSocketApp
from supervisoragent.systemstat import stats


START = 'start'
STOP = 'stop'
RESTART = 'restart'


class WebSocketConnection(object):
    push_interval = 0.0
    thread = None
    is_connected = False
    connection = None
    process_monitor = None
    rpc = None

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
            command = msg['cmd'].split(' ')[0]
            args = msg['cmd'].split(' ')[1:]

            if command == START:
                cls.rpc.startProcesses(args)
            elif command == STOP:
                cls.rpc.stopProcesses(args)
            elif command == RESTART:
                cls.rpc.restartProcesses(args)

    @classmethod
    def on_error(cls, ws, error):
        print error

    @classmethod
    def on_close(cls, ws):
        cls.is_connected = False
        cls.connection = None
        print "### closed ###"

    @classmethod
    def on_open(cls, ws):
        cls.is_connected = True
        cls.connection = ws
        ws.send(json.dumps({'system': stats()}))

        def push_stats(*args):
            while cls.is_connected:
                ws.send(json.dumps(cls.process_monitor.snapshot()))
                cls.process_monitor.reset()
                time.sleep(cls.push_interval)

        cls.thread = Thread(target=push_stats)
        cls.thread.start()
        print('Finished with on_open')


class WebsocketManager():

    def __init__(self, rpc, process_monitor, push_interval,
                 url, token, **kwargs):
        parsed = urlparse(url)
        if parsed.scheme not in ['ws', 'wss']:
            raise ValueError(
                'Websocket scheme "ws" or "wss" not provided in url.')

        self.thread = Thread(target=self.run_socket,
                             args=([rpc, process_monitor, push_interval,
                                    url, token]))
        self.thread.daemon = True

    def start(self):
        self.thread.start()

    def run_socket(self, rpc, process_monitor, push_interval, url, token):
        while True:
            try:
                print('WebsocketManager.run_socket: create_connection')
                WebSocketConnection.process_monitor = process_monitor
                WebSocketConnection.push_interval = push_interval
                WebSocketConnection.rpc = rpc
                ws = WebSocketApp('{0}/supervisor/'.format(url.strip('/')),
                                  header=['authorization: {0}'.format(token)],
                                  on_message=WebSocketConnection.on_message,
                                  on_error=WebSocketConnection.on_error,
                                  on_open=WebSocketConnection.on_open,
                                  on_close=WebSocketConnection.on_close)
                ws.run_forever()
            except Exception as e:
                print("Exception: %s" % e)
            time.sleep(60)  # Wait 60 seconds before attemping to reconnect
