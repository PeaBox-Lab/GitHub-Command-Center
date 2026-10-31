import unittest
from github_command_center.services.startup_profiler import StartupProfiler
class StartupProfilerTests(unittest.TestCase):
 def test_default_probes(self):
  values=StartupProfiler().run();self.assertEqual(len(values),5);self.assertTrue(all(x.ok for x in values));self.assertGreaterEqual(StartupProfiler.total(values),0)
 def test_failure_captured(self):self.assertFalse(StartupProfiler().time_import("module_that_does_not_exist_xyz").ok)
 def test_serializable(self):self.assertIn("seconds",StartupProfiler.serializable(StartupProfiler().run(["github_command_center.models"]))[0])
