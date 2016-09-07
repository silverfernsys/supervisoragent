#! /usr/bin/env python
import signal
import sys
import time
from configutil import ConfigError
from config.agent import config
from setproctitle import setproctitle
from rpc import RPC, RPCError
from eventmonitor import EventMonitor
from log import config_logging, LoggingError
from processmonitor import ProcessMonitor
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
        try:
            self.config.parse()
        except ConfigError as e:
            print(e)
            sys.exit(1)
        try:
            config_logging(config.arguments.supervisor.log_level,
                config.arguments.supervisor.log_file)
        except LoggingError as e:
            print(e)
            sys.exit(1)

    def run(self):
        self.run_loop = True
        rpc = RPC()
        process_monitor = ProcessMonitor(rpc, self.config.arguments.supervisor.sample_interval)
        process_monitor.start()
        event_monitor = EventMonitor(process_monitor)
        event_monitor.start()
        websocket_manager = WebsocketManager(
            rpc, process_monitor, **vars(self.config.arguments.supervisor))
        websocket_manager.start()
        rpc.restartProcesses(['agenteventlistener'])

        while self.run_loop:
            time.sleep(0.1)


def main():
    try:
        agent = Agent(config)
        agent.run()
    except RPCError as e:
        if e.errno == 2:
            print('{0} Please check to see if supervisor is running. '
                  'Exiting'.format(e.message))
        elif e.errno == 13:
            print('{0} Please run agent as root. Exiting'.format(e.message))
        else:
            print('{0} Exiting.'.format(e.message))
        sys.exit(1)
    except LoggingError as e:
        print('{0} Please run agent as root. Exiting.'.format(e.message))
        sys.exit(1)
    except Exception as e:
        print('{0} Exiting.'.format(e.message))
        sys.exit(1)


if __name__ == "__main__":
    main()
