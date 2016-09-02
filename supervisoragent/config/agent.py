from os.path import dirname, join, expanduser
from base import Config


class AgentConfig(Config):
    possible_args = [
        ('sample_interval', float),
        ('push_interval', float),
        ('token', str),
        ('url', str),
        ('log_level', str),
        ('log_file', str),
    ]

    config_search_paths = [
        join(dirname(__file__), 'supervisoragent.conf'),
        expanduser('~/supervisoragent.conf'),
        '/etc/supervisoragent/supervisoragent.conf'
    ]

    config_name = 'supervisor'

    def config_parser(self, parser):
        parser.add_argument("--config", help="configuration file to read")
        parser.add_argument("--sample_interval",
                            help="how often to sample metrics (in seconds)")
        parser.add_argument("--push_interval",
                            help="how often to push data "
                                 "to server (in seconds)")
        parser.add_argument("--token", help="the authorization token to use")
        parser.add_argument("--url", help="the server url to use")
        parser.add_argument("--log_level", help="log level to use")
        parser.add_argument("--log_file", help="log file to use")


config = AgentConfig()
