#! /usr/bin/env python
import argparse
import logging
import signal
import time
import ConfigParser
from setproctitle import setproctitle
from processmonitor import ProcessMonitor
from statusserver import StatusServer


AGENT_VERSION = '0.0.1'

class Agent(object):
    def shutdown(self, sig, frame):
        self.run_loop = False

    def __init__(self, config_data):
        self.run_loop = True
        self.start_time = time.time()
        setproctitle('supervisoragent')
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        self.config_data = config_data

    def run(self):
        self.run_loop = True
        processmonitor = ProcessMonitor(sample_interval=self.config_data['sample_interval'],
            push_interval=self.config_data['push_interval'],
            token=self.config_data['token'], url=self.config_data['url'])
        statusserver = StatusServer(self.config_data['port'], self)
        while self.run_loop:
            time.sleep(0.1)

    def data(self):
        ret_data = self.config_data.copy()
        ret_data['supervisor_version'] = ProcessMonitor.version
        ret_data['start_time'] = self.start_time
        ret_data['agent_version'] = AGENT_VERSION
        return ret_data
        
        # We're going to shutdown here
        # statusserver.shutdown()


def resolveConfig(config, args):
    """
    Returns a dictionary consisting of keys found
    in config and the values of config overwritten
    by values of args
    """
    data = {}
    data['sample_interval'] = args.sample_interval or config.getint('supervisor', 'sample_interval')
    data['push_interval'] = args.push_interval or config.getint('supervisor', 'push_interval')
    data['token'] = args.token or config.get('supervisor', 'token')
    data['url'] = args.url or config.get('supervisor', 'url')
    data['log_level'] = args.log_level or config.get('supervisor', 'log_level')
    data['log_file'] = args.log_file or config.get('supervisor', 'log_file')
    data['database'] = args.database or config.get('supervisor', 'database')
    data['port'] = args.port or config.getint('supervisor', 'port')
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="configuration file to read. /etc/supervisoragent/supervisoragent.conf otherwise")
    parser.add_argument("--sample_interval", help="how often to sample metrics (in seconds)")
    parser.add_argument("--push_interval", help="how often to push data to server (in seconds)")
    parser.add_argument("--token", help="the authorization token to use")
    parser.add_argument("--url", help="the server url to use")
    parser.add_argument("--log_level", help="log level to use")
    parser.add_argument("--log_file", help="log file to use")
    parser.add_argument("--database", help="the database connection to use")
    parser.add_argument("--port", help="the port number to serve status on")
    args = parser.parse_args()

    # try:
    config = ConfigParser.ConfigParser()
    config_file_path = args.config or '/etc/supervisoragent/supervisoragent.conf'
    config.read(config_file_path)
    config_data = resolveConfig(config, args)
    logging.basicConfig(filename=config_data['log_file'], format='%(asctime)s::%(levelname)s::%(name)s::%(message)s', level=logging.DEBUG)
    agent = Agent(config_data)
    agent.run()
    # except Exception as e:
        # print('Error loading configuration file at %s.' % config_file_path)
        # print('DETAILS: %s' % e)


if __name__ == "__main__":
    main()