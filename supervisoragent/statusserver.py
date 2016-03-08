import SimpleHTTPServer
import SocketServer
import json
import threading
from BaseHTTPServer import BaseHTTPRequestHandler
# from agent import Agent


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status/":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(StatusServer.get_agent().data()))


class StatusServer(object):
    agent = None

    @staticmethod
    def get_agent():
        return StatusServer.agent

    def __init__(self, port, agent):
        self.port = port
        StatusServer.agent = agent
        server_thread = threading.Thread(target=self.status_server, args=())
        server_thread.daemon = True
        server_thread.start()

    def status_server(self):
        self.httpd = SocketServer.TCPServer(("", self.port), StatusHandler)
        self.httpd.serve_forever()

    def shutdown(self):
        self.httpd.shutdown()
