from __future__ import annotations
import subprocess, tempfile, unittest
from pathlib import Path
from github_command_center.services import GitCommandError, GitService

class GitServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.repo=Path(self.temp.name)
        subprocess.run(["git","init","-q","-b","main"],cwd=self.repo,check=True)
        subprocess.run(["git","config","user.name","Test User"],cwd=self.repo,check=True)
        subprocess.run(["git","config","user.email","test@example.com"],cwd=self.repo,check=True)
        (self.repo/"README.md").write_text("hello\n",encoding="utf-8")
        subprocess.run(["git","add","README.md"],cwd=self.repo,check=True)
        subprocess.run(["git","commit","-q","-m","feat: initial commit"],cwd=self.repo,check=True)
        self.git=GitService(self.repo)
    def tearDown(self):self.temp.cleanup()
    def test_repository_state_clean(self):
        state=self.git.repository_state();self.assertEqual(state.branch,"main");self.assertTrue(state.clean);self.assertEqual(len(state.head),40)
    def test_repository_state_changed(self):
        (self.repo/"README.md").write_text("changed\n",encoding="utf-8");state=self.git.repository_state();self.assertFalse(state.clean);self.assertTrue(any("README.md" in x for x in state.changed_paths))
    def test_verify_ref(self):self.assertEqual(len(self.git.verify_ref("HEAD","commit")),40)
    def test_failure_raises_typed_error(self):
        with self.assertRaises(GitCommandError):self.git.execute("rev-parse","refs/heads/missing")
    def test_no_shell_interpolation(self):self.assertFalse(self.git.execute("rev-parse","--verify","HEAD;echo unsafe",check=False).ok)
if __name__=="__main__":unittest.main()
