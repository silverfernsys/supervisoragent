#! /usr/bin/env python
import signal
import time
from config import config
from setproctitle import setproctitle
from rpc import RPC
from eventmonitor import EventMonitor
from processmonitor import ProcessMonitor
from statusserver import StatusServer
from ws import WebsocketManager

AGENT_VERSION = '0.0.1'


class Agent(object):
    def shutdown(self, sig, frame):
        self.run_loop = False

    def __init__(self, config):
        self.run_loop = True
        self.start_time = time.time()
        setproctitle('supervisoragent')
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        self.config = config

    def run(self):
        self.run_loop = True
        rpc = RPC()
        process_monitor = ProcessMonitor(rpc, self.config.sample_interval)
        process_monitor.start()
        event_monitor = EventMonitor(process_monitor)
        event_monitor.start()
        websocket_manager = WebsocketManager(rpc, process_monitor, **vars(self.config))
        websocket_manager.start()
        rpc.restartProcesses(['agenteventlistener'])

        while self.run_loop:
            time.sleep(0.1)

    def data(self):
        ret_data = self.config.__dict__()
        ret_data['supervisor_version'] = ProcessMonitor.version
        ret_data['start_time'] = self.start_time
        ret_data['agent_version'] = AGENT_VERSION
        return ret_data


def main():
    agent = Agent(config)
    agent.run()


if __name__ == "__main__":
    main()