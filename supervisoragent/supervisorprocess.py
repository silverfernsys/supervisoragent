#!/usr/bin/env python
from procstat import CPUStats, MemoryStats
from systemstat import stats
from time import time

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

class SupervisorProcess(object):
    processes = {}

    def __init__(self, name, group, pid, state, statename, start):
        self.name = name
        self.group = group
        self._pid = pid
        self._state = state
        self._statename = statename
        self.start = start
        self.stats = []
        self.cpu_stats = CPUStats(self.pid)
        self.mem_stats = MemoryStats(self.pid)

        self.add(self)

    @property
    def state(self):
        return self._state

    @property
    def statename(self):
        return self._statename
    
    @statename.setter
    def statename(self, val):
        try:
            self._statename = val
            self._state = STATE_MAP[val]
        except Exception as e:
            print(e)

    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, val):
        self._pid = val
        self.cpu_stats.pid = val
        self.mem_stats.pid = val

    def update(self):
        timestamp = time()
        user_util, sys_util = self.cpu_stats.cpu_percent_change()
        memory = self.mem_stats.memory()
        self.stats.append([timestamp, user_util, memory])

    def state_update(self):
        return {'state_update': {'name': self.name,
            'group': self.group, 'pid': self._pid,
            'state': self._state, 'statename': self._statename,
            'start': self.start } }

    @classmethod
    def system_stats(cls):
        return {'system_stats': stats()}
    
    def _binary_search_helper(self, array, value, start, end):
        if (start >= end):
            return end
        else:
            mid = start + (end - start) / 2
            if array[mid][0] > value:
                return self._binary_search_helper(array, value, start, mid)
            else:
                return self._binary_search_helper(array, value, mid + 1, end)

    def _binary_search(self, array, value):
        index = self._binary_search_helper(array, value, 0, len(array))
        return array[index:len(array)]

    def get_stats(self, time=None):
        if time is None:
            return self.stats
        else:
            return self._binary_search(self.stats, time)

    def __repr__(self):
        return 'name: {self.name}, group: {self.group}, pid: {self._pid}, ' \
            'stats: {self.stats}'.format(self=self)

    def __json__(self):
        return {'name': self.name, 'group': self.group,
            'pid': self._pid, 'state': self._state,
            'start': self.start, 'stats': self.stats, 
            'statename': self._statename }

    def reset(self):
        self.stats = []

    @classmethod
    def get(self, group, name):
        try:
            return self.processes[group][name]
        except:
            None

    @classmethod
    def add(self, proc):
        if proc.group not in self.processes:
            self.processes[proc.group] = {}
        self.processes[proc.group][proc.name] = proc

    # A class method generator that yields the contents of the 'processes' dictionary
    @classmethod
    def all(self):
        for group in self.processes:
            for name in self.processes[group]:
                yield self.processes[group][name]
        raise StopIteration()

    @classmethod
    def updateall(self):
        for p in self.all():
            p.update()

    @classmethod
    def snapshot_update(cls):
        return {'snapshot_update': [p.__json__() for p in cls.all()]}

    @classmethod
    def reset_all(self):
        for p in self.all():
            p.reset()

    @classmethod
    def purge(self):
        self.processes = {}
