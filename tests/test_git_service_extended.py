import subprocess,tempfile,unittest
from pathlib import Path
from github_command_center.services import GitService

class ExtendedGitServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.repo=Path(self.tmp.name);subprocess.run(["git","init","-q","-b","main"],cwd=self.repo,check=True);subprocess.run(["git","config","user.name","Test"],cwd=self.repo,check=True);subprocess.run(["git","config","user.email","t@example.com"],cwd=self.repo,check=True);(self.repo/"a.txt").write_text("a\n");subprocess.run(["git","add","."],cwd=self.repo,check=True);subprocess.run(["git","commit","-qm","init"],cwd=self.repo,check=True);self.git=GitService(self.repo)
    def tearDown(self):self.tmp.cleanup()
    def test_lines(self):self.assertEqual(self.git.lines("branch","--show-current"),["main"])
    def test_clean_guard(self):self.git.ensure_clean()
    def test_dirty_guard(self):
        (self.repo/"a.txt").write_text("b\n")
        with self.assertRaises(RuntimeError):self.git.ensure_clean()
    def test_safety_branch(self):self.git.create_safety_branch("backup/test");self.assertEqual(len(self.git.verify_ref("backup/test")),40)
    def test_nonchecking_result(self):self.assertFalse(self.git.execute("show","missing-ref",check=False).ok)
if __name__=="__main__":unittest.main()
