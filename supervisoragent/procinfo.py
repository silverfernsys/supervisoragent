#!/usr/bin/env python
from procstat import CPUStats, MemoryStats
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

class ProcInfo(object):
    processes = {}

    def __init__(self, name, group, pid, state, statename, start):
        self.name = name
        self.group = group
        self._pid = pid
        self._state = state
        self._statename = statename
        self.start = start
        self.cpu = []
        self.mem = []
        self.cpu_stats = CPUStats(self.pid)
        self.mem_stats = MemoryStats(self.pid)

        ProcInfo.add(self)

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
        memory_percent = self.mem_stats.memory_percent()
        self.cpu.append([timestamp, user_util])
        self.mem.append([timestamp, memory_percent])
    
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

    def get_cpu(self, time=None):
        if time is None:
            return self.cpu
        else:
            return self._binary_search(self.cpu, time)

    def get_mem(self, time=None):
        if time is None:
            return self.mem
        else:
            return self._binary_search(self.mem, time)

    def __str__(self):
        return 'name: %s, group: %s, pid: %s, cpu: %s, mem: %s' % (self.name, self.group, self._pid, self.cpu, self.mem)

    def to_dict(self):
        return {'name': self.name,
        'group': self.group,
        'pid': self._pid,
        'state': self._state,
        'statename': self._statename,
        'start': self.start,
        'cpu': self.cpu,
        'mem': self.mem,
        }

    @classmethod
    def get(self, group, name):
        try:
            return ProcInfo.processes[group][name]
        except:
            None

    @classmethod
    def add(self, proc):
        if proc.group not in ProcInfo.processes:
            ProcInfo.processes[proc.group] = {}
        ProcInfo.processes[proc.group][proc.name] = proc

    # A class method generator that yields the contents of the 'processes' dictionary
    @classmethod
    def all(self):
        for group in ProcInfo.processes:
            for name in ProcInfo.processes[group]:
                yield ProcInfo.processes[group][name]
        raise StopIteration()

    @classmethod
    def updateall(self):
        for p in ProcInfo.all():
            p.update()

    @classmethod
    def purge(self):
        ProcInfo.processes = {}
