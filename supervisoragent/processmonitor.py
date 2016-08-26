#!/usr/bin/env python
from time import time, sleep
from threading import Thread
from procstat import CPUStats, MemoryStats
from ws import WebSocketConnection
from systemstat import stats

STATE_MAP = {
    'STOPPED': 0,
    'STARTING': 10,
    'RUNNING': 20,
    'BACKOFF': 30,
    'STOPPING': 40,
    'EXITED': 100,
    'FATAL': 200,
    'UNKNOWN': 1000 
}

class ProcessMonitor(object):
    def __init__(self, rpc, sample_interval):
        self.processes = {}
        self.rpc = rpc
        self.sample_interval = sample_interval
        self.get_processes()

    def get_processes(self):
        data = self.rpc.xmlrpc.supervisor.getAllProcessInfo()
        for row in data:
            process = SupervisorProcess(**row)
            self.processes[(process.name, process.group)] = process

    def start(self):
        thread = Thread(target=self.monitor)
        thread.daemon = True
        thread.start()

    # {u'from_state': u'BACKOFF', u'group': u'agenteventlistener', u'name': u'agenteventlistener',
    # u'statename': u'STARTING', u'pid': None, u'eventname': u'PROCESS_STATE_STARTING'}
    def update(self, name, group, pid, statename, from_state, eventname, **kwargs):
        info = self.rpc.xmlrpc.supervisor.getProcessInfo(name)
        process = self.processes.get((name, group))
        process.update(pid, statename, info['start'])
        if WebSocketConnection.is_connected:
            print('STATE_UPDATE: data = %s' % process.state_update())
            WebSocketConnection.connection.send(json.dumps(process.state_update()))

    def snapshot(self):
        return {'snapshot': [p.__json__() for p in self.processes.values()]}

    def reset(self):
        for p in self.processes.values():
            p.reset()

    def sample(self):
        for p in self.processes.values():
            p.sample()

    def monitor(self):
        while True:
            self.sample()
            sleep(self.sample_interval)

    def __repr__(self):
        return '<Manager ({0})'.format(', '.join(str(p) for p in self.processes.values()))


class SupervisorProcess(object):
    def __init__(self, name, group, pid, state, statename, start, **kwargs):
        self.name = name
        self.group = group
        if statename == 'STOPPED':
            self.pid = None
        else:
            self.pid = int(pid)
        self.state = state
        self.statename = statename
        self.start = start
        self.stats = []
        self.cpu_stats = CPUStats(self.pid)
        self.mem_stats = MemoryStats(self.pid)

    def update(self, pid, statename, start, **kwargs):
        if statename == 'STOPPED':
            self.pid = None
            self.cpu_stats = None
            self.mem_stats = None
        else:
            if pid != self.pid:
                self.pid = pid
                self.cpu_stats = CPUStats(pid)
                self.mem_stats = MemoryStats(pid)
        self.statename = statename
        self.state = STATE_MAP[statename]
        self.start = start

    def sample(self):
        timestamp = time()
        if self.cpu_stats:
            user_util, sys_util = self.cpu_stats.cpu_percent_change()
        else:
            user_util, sys_util = (0.0, 0.0)

        if self.mem_stats:
            memory = self.mem_stats.memory()
        else:
            memory = 0

        self.stats.append([timestamp, user_util, memory])

    def reset(self):
        self.stats = []

    def state_update(self):
        return {'state': {'name': self.name,
            'group': self.group, 'pid': self.pid,
            'state': self.state, 'statename': self.statename,
            'start': self.start } }

    def __repr__(self):
        return '<SupervisorProcess (name: {self.name}, group: {self.group}, pid: {self.pid}, ' \
            'start: {self.start}, state: {self.state}, statename: {self.statename}, ' \
            'stats: {self.stats})'.format(self=self)

    def __json__(self):
        return {'name': self.name, 'group': self.group,
            'pid': self.pid, 'state': self.state,
            'start': self.start, 'stats': self.stats, 
            'statename': self.statename }
