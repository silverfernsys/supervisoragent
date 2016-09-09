import unittest
from time import time
from supervisoragent.processmonitor import (ProcessMonitor,
    SupervisorProcess)


class SupervisorProcessTest(unittest.TestCase):
    pass

    # def setUp(self):
    #     self.processmonitor = ProcessMonitor(rpc=None, sample_interval=1)
    #     self.proc_0 = SupervisorProcess(
    #         'soffice', 'soffice', None, 0, 'STOPPED', 1.000)
    #     self.proc_1 = SupervisorProcess(
    #         'sremote', 'sremote', 9123, 0, 'STOPPED', 1.000)

    # def tearDown(self):
    #     pass

    # def test_get(self):
    #     self.assertEqual(self.proc_0, SupervisorProcess.get(
    #         'soffice', 'soffice'), "get works")
    #     self.assertEqual(self.proc_1, SupervisorProcess.get(
    #         'sremote', 'sremote'), "get works")

    # def test_update_all(self):
    #     before_count_proc_0 = len(self.proc_0.stats)
    #     before_count_proc_1 = len(self.proc_1.stats)
    #     SupervisorProcess.update_all()
    #     SupervisorProcess.update_all()
    #     SupervisorProcess.update_all()
    #     after_count_proc_0 = len(self.proc_0.stats)
    #     after_count_proc_1 = len(self.proc_1.stats)
    #     self.assertEqual(before_count_proc_0 + 3, after_count_proc_0)
    #     self.assertEqual(before_count_proc_1 + 3, after_count_proc_1)

    # def test_stats_filter(self):
    #     SupervisorProcess.update_all()
    #     SupervisorProcess.update_all()
    #     SupervisorProcess.update_all()
    #     timestamp = time()
    #     SupervisorProcess.update_all()
    #     SupervisorProcess.update_all()
    #     SupervisorProcess.update_all()
    #     self.assertEqual(len(self.proc_0.get_stats(timestamp)), 3)
    #     self.assertEqual(len(self.proc_1.get_stats(timestamp)), 3)

    # def test_statename_change(self):
    #     self.assertEqual(self.proc_0.state, 0)
    #     self.proc_0.statename = 'STARTING'
    #     self.assertEqual(self.proc_0.state, 10)
    #     self.proc_0.statename = 'RUNNING'
    #     self.assertEqual(self.proc_0.state, 20)
    #     self.proc_0.statename = 'BACKOFF'
    #     self.assertEqual(self.proc_0.state, 30)
    #     self.proc_0.statename = 'STOPPING'
    #     self.assertEqual(self.proc_0.state, 40)
    #     self.proc_0.statename = 'EXITED'
    #     self.assertEqual(self.proc_0.state, 100)
    #     self.proc_0.statename = 'FATAL'
    #     self.assertEqual(self.proc_0.state, 200)
    #     self.proc_0.statename = 'UNKNOWN'
    #     self.assertEqual(self.proc_0.state, 1000)
