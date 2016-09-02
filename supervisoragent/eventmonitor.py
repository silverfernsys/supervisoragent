import json
import os
import socket
from logging import getLogger
from threading import Thread


class EventMonitor(object):

    def __init__(self, process_monitor):
        self.process_monitor = process_monitor

    def start(self):
        thread = Thread(target=self.monitor, args=())
        thread.daemon = True
        thread.start()

    def monitor(self):
        logger = getLogger('Event Server')
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
                    headers = dict([x.split(':') for x in line.split()])
                    data = handle.read(int(headers['LENGTH']))
                    json_data = json.loads(data)
                    self.process_monitor.update(**json_data)
            except Exception as e:
                print('Exception: %s' % e)
                print('Closing connection...')
                logger.info('Closing connection...')
                connection.close()
                logger.info('Connection closed.')
