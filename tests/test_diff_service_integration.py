import subprocess,tempfile,unittest
from pathlib import Path
from github_command_center.services.diff_service import DiffService
class DiffIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.repo=Path(self.tmp.name);subprocess.run(["git","init","-q","-b","main"],cwd=self.repo,check=True);subprocess.run(["git","config","user.name","T"],cwd=self.repo,check=True);subprocess.run(["git","config","user.email","t@e.com"],cwd=self.repo,check=True);(self.repo/"a.txt").write_text("one\ntwo\n");subprocess.run(["git","add","."],cwd=self.repo,check=True);subprocess.run(["git","commit","-qm","init"],cwd=self.repo,check=True);self.service=DiffService(self.repo)
 def tearDown(self):self.tmp.cleanup()
 def test_working_diff(self):
  (self.repo/"a.txt").write_text("one\nchanged\n");files=self.service.files();self.assertEqual(files[0].path,"a.txt");self.assertEqual(files[0].additions,1)
 def test_stage_hunk(self):
  (self.repo/"a.txt").write_text("one\nchanged\n");f=self.service.files()[0];self.service.apply_patch(self.service.hunk_patch(f,f.hunks[0]));staged=subprocess.run(["git","diff","--cached","--name-only"],cwd=self.repo,text=True,capture_output=True,check=True).stdout;self.assertIn("a.txt",staged)
