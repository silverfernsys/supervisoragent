import mock
import os
import subprocess
import unittest
from supervisoragent.procstat import CPUStats, MemoryStats


class ProcStatTest(unittest.TestCase):

    def setUp(self):
        self.cpu = CPUStats(1)
        self.mem = MemoryStats(1)
        self.resources = os.path.join(os.path.abspath(
            os.path.dirname(__file__)), 'resources')

    def tearDown(self):
        self.cpu = None
        self.mem = None

    @mock.patch.object(subprocess, 'Popen')
    def test_cpu(self, mock_popen):
        proc_id_stat = open(os.path.join(
            self.resources, 'proc_id_stat.txt')).read()
        proc_stat = open(os.path.join(self.resources, 'proc_stat.txt')).read()
        mock_popen.return_value.returncode.side_effect = [0, 0, 0, 0]
        side_effects = [(proc_id_stat, "Error1"), (proc_stat, "Error2"),
                        (proc_id_stat, "Error3"), (proc_stat, "Error4"),
                        (proc_id_stat, "Error5"), (proc_stat, "Error6")]
        mock_popen.return_value.communicate.side_effect = side_effects
        (user_util, sys_util) = self.cpu.cpu_percent()
        self.cpu.cpu_percent_change()
        (user_util_change, sys_util_change) = self.cpu.cpu_percent_change()
        self.assertEqual(user_util_change, 0, "Percent change is zero.")
        self.assertEqual(sys_util_change, 0, "Percent change is zero.")

    @mock.patch.object(subprocess, 'Popen')
    def test_mem(self, mock_popen):
        proc_id_smaps = open(os.path.join(
            self.resources, 'proc_id_smaps.txt')).read()
        proc_meminfo = open(os.path.join(
            self.resources, 'proc_meminfo.txt')).read()
        mock_popen.return_value.returncode.side_effect = [0, 0, 0, 0]
        side_effects = [(proc_id_smaps, "Error1"), (proc_meminfo, "Error2"),
                        (proc_id_smaps, "Error3"), (proc_meminfo, "Error4")]
        mock_popen.return_value.communicate.side_effect = side_effects
        (memory_used, memory_total,
         free_mem, cached, cached_swap,
         total_swap, free_swap) = self.mem.__stat__()
        mem_percent = 100 * float(memory_used) / float(memory_total)
        memory_percent = self.mem.memory_percent()
        self.assertEqual(mem_percent, memory_percent)
