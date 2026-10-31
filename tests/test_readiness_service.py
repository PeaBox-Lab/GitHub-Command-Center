import subprocess,tempfile,unittest
from pathlib import Path
from github_command_center.services.readiness_service import ReadinessReport,ReadinessService

class ReadinessTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);subprocess.run(["git","init","-q","-b","main"],cwd=self.p,check=True);subprocess.run(["git","config","user.name","T"],cwd=self.p,check=True);subprocess.run(["git","config","user.email","t@e.com"],cwd=self.p,check=True)
  for name in ReadinessService.REQUIRED_FILES:(self.p/name).write_text(name)
  subprocess.run(["git","add","."],cwd=self.p,check=True);subprocess.run(["git","commit","-qm","init"],cwd=self.p,check=True)
 def tearDown(self):self.tmp.cleanup()
 def test_clean_repo_core_checks(self):
  r=ReadinessService(self.p).assess();self.assertTrue(next(c for c in r.checks if c.name=="Working tree").status=="PASS");self.assertGreater(r.score,50)
 def test_dirty_fails_required(self):(self.p/"README.md").write_text("changed");self.assertFalse(ReadinessService(self.p).assess().passed)
 def test_missing_doc_fails(self):(self.p/"SECURITY.md").unlink();self.assertFalse(ReadinessService(self.p).assess().passed)
 def test_json(self):self.assertIn('"score"',ReadinessService(self.p).assess().to_json())
 def test_empty_report_score(self):self.assertEqual(ReadinessReport("x").score,0)
