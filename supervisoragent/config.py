import sys, logging
from argparse import ArgumentParser
from ConfigParser import SafeConfigParser
from os.path import dirname, join, expanduser


log_vals = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING, 
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG, 
    'NOTSET': logging.NOTSET }


class Config(object):
    possible_args = [
        ('sample_interval', float),
        ('push_interval', float),
        ('token', str),
        ('url', str),
        ('log_level', str),
        ('log_file', str),
        ('database', str), 
        ('port', int),
    ]

    config_search_paths = [
        join(dirname(__file__), 'supervisoragent.conf'),
        expanduser('~/supervisoragent.conf'),
        '/etc/supervisoragent/supervisoragent.conf'
    ]

    def __init__(self):
        self.loadConfig()
        self.initLogging()

    def loadConfig(self):
        try:
            parser = ArgumentParser()
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

            config_parser = SafeConfigParser()
            if args.config:
                paths = [args.config]
            else:
                paths = self.config_search_paths

            config_parser.read(paths)

            data = {p: f(getattr(args, p, None) or config_parser.get('supervisor', p)) for (p, f) in self.possible_args}

            for (arg, _type) in self.possible_args:
                if arg not in data:
                    print('Missing configuration argument {0}. Exiting.\n'.format(arg))
                    sys.exit(1)

            self.__dict__.update(data)
        except Exception as e:
            print('Error loading configuration files at {0}.\nEXCEPTION DETAILS: {1}'.format(paths, e))

    def initLogging(self):
        logging.basicConfig(filename=self.log_file,
            format='%(asctime)s::%(levelname)s::%(name)s::%(message)s',
            level=log_vals.get(self.log_level, logging.DEBUG))

    def __repr__(self):
        return '<Config({0}>'.format(', '.join('%s=%r' % (k, v)
            for (k, v) in self.__dict__.iteritems()))


config = Config()
