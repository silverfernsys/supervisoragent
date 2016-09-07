from os.path import dirname, join, expanduser
from configutil import Config

config = Config()
config.add_paths([join(dirname(__file__), 'supervisoragent.conf'),
    expanduser('~/supervisoragent.conf'),
    '/etc/supervisoragent/supervisoragent.conf'
])

section = config.add_section('supervisor')
section.add_argument('sample_interval', 'how often to sample metrics (in seconds)', type=float)
section.add_argument('push_interval', 'how often to push data to server (in seconds)', type=float)
section.add_argument('token', 'the authorization token to use')
section.add_argument('url', 'the server url to use')
section.add_argument('log_level', 'log level',
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
section.add_argument('log_file', 'log file path')
