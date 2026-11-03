import subprocess,tempfile,unittest
from pathlib import Path
from github_command_center.services.health_snapshot import HealthSnapshotService
class HealthSnapshotTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.p=Path(self.t.name);subprocess.run(['git','init','-q','-b','main'],cwd=self.p,check=True);subprocess.run(['git','config','user.name','T'],cwd=self.p,check=True);subprocess.run(['git','config','user.email','t@e.com'],cwd=self.p,check=True);(self.p/'a').write_text('a');subprocess.run(['git','add','.'],cwd=self.p,check=True);subprocess.run(['git','commit','-qm','init'],cwd=self.p,check=True)
 def tearDown(self):self.t.cleanup()
 def test_capture(self):
  x=HealthSnapshotService(self.p).capture();self.assertEqual(x.branch,'main');self.assertTrue(x.clean);self.assertEqual(x.changed,0)
 def test_json(self):self.assertIn('"branch": "main"',HealthSnapshotService.to_json(HealthSnapshotService(self.p).capture()))

