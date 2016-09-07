import logging

log_vals = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET}


class LoggingError(Exception):

    def __init__(self, arg):
        self.message = 'LoggingError: {0}'.format(arg)
        self.arg = arg


class LogFileError(LoggingError):

    def __init__(self, arg):
        self.message = 'Error opening log file "{0}".'.format(arg)
        self.arg = arg


def config_logging(log_level, log_file):
    try:
        format = '%(asctime)s::%(levelname)s::%(name)s::%(message)s'
        level = log_vals.get(log_level, logging.DEBUG)
        logging.basicConfig(filename=log_file,
                            format=format, level=level)
    except IOError:
        raise LogFileError(log_file)
