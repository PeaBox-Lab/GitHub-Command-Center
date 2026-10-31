import tempfile,subprocess,unittest
from pathlib import Path
from github_command_center.services.reliability import ReliabilityService
class ReliabilityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name);subprocess.run(["git","init","-q","-b","main"],cwd=self.path,check=True);subprocess.run(["git","config","user.name","T"],cwd=self.path,check=True);subprocess.run(["git","config","user.email","t@e.com"],cwd=self.path,check=True);(self.path/"a").write_text("a");subprocess.run(["git","add","."],cwd=self.path,check=True);subprocess.run(["git","commit","-qm","init"],cwd=self.path,check=True)
 def tearDown(self):self.tmp.cleanup()
 def test_standard_probes(self):
  values=ReliabilityService(self.path).standard_probes();self.assertEqual(len(values),4);self.assertTrue(all(v.ok for v in values));self.assertTrue(all(v.seconds>=0 for v in values))
 def test_failed_probe(self):self.assertFalse(ReliabilityService(self.path).time_call("bad",lambda:(_ for _ in ()).throw(RuntimeError("x"))).ok)
