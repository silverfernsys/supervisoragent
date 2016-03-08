##############################################################################
#
# Copyright (c) 2016 SilverFern Systems.
# All Rights Reserved.
#
# This software is subject to the provisions of the BSD-like license at
# http://www.repoze.org/LICENSE.txt.  A copy of the license should accompany
# this distribution.  THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL
# EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND
# FITNESS FOR A PARTICULAR PURPOSE
#
##############################################################################

import os
import sys

py_version = sys.version_info[:2]

if py_version < (2, 6):
    raise RuntimeError('On Python 2, Supervisor requires Python 2.6 or later')
elif (3, 0) < py_version < (3, 2):
    raise RuntimeError('On Python 3, Supervisor requires Python 3.2 or later')

requires = ['websocket-client>=0.35.0']
tests_require = []
if py_version < (3, 3):
    tests_require.append('mock')

testing_extras = tests_require + [
    'pytest',
    'pytest-cov',
    ]

from setuptools import setup, find_packages
here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
    CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()
except:
    README = """\
Supervisor-agent is a process that monitors supervisor processes
and sends their state to an upstream server as specified in the
config file. """
    CHANGES = ''

# https://pypi.python.org/pypi?%3Aaction=list_classifiers
CLASSIFIERS = [
    'Development Status :: 1 - Planning',
    'Environment :: No Input/Output (Daemon)',
    'Intended Audience :: System Administrators',
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Topic :: System :: Boot',
    'Topic :: System :: Monitoring',
    'Topic :: System :: Systems Administration',
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.6",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.2",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Programming Language :: Python :: 3.5",
]

version_txt = os.path.join(here, 'supervisoragent/version.txt')
supervisor_agent_version = open(version_txt).read().strip()

dist = setup(
    name='supervisoragent',
    version=supervisor_agent_version,
    license='BSD 2, (https://opensource.org/licenses/BSD-2-Clause)',
    url='http://silverfern.io/supervisoragent',
    description="A system for monitoring and controlling process state under UNIX",
    long_description=README + '\n\n' + CHANGES,
    classifiers=CLASSIFIERS,
    author="Marc Wilson",
    author_email="marcw@silverfern.io",
    maintainer="Marc Wilson",
    maintainer_email="marcw@silverfern.io",
    packages=find_packages(),
    install_requires=requires,
    extras_require={
        # 'iterparse': ['cElementTree >= 1.0.2'],
        'testing': testing_extras,
        },
    tests_require=tests_require,
    include_package_data=True,
    zip_safe=False,
    test_suite="supervisor-agent.tests",
    entry_points={
        'console_scripts': [
            'supervisoragent = supervisoragent.agent:main',
            'supervisoragentcfg = supervisoragent.agentcfg:main',
        ],
    },
    # https://docs.python.org/2/distutils/setupscript.html#installing-additional-files
    data_files=[('/etc/supervisoragent', ['scripts/conf/supervisoragent.conf'])]
)