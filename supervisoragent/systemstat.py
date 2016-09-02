#! /usr/bin/env python

import multiprocessing
import os
import platform
import socket


def stats():
    """
    Return a dictionary containing hostname,
    processor type, cpu count, total memory,
    linux distribution name, and distribution version.
    """
    (dist_name, dist_version, _) = platform.linux_distribution()

    return {
        'hostname': socket.getfqdn(),
        'processor': platform.processor(),
        'num_cores': multiprocessing.cpu_count(),
        'memory': os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"),
        'dist_name': dist_name,
        'dist_version': dist_version
    }
