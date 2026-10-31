import unittest
from tests.git_fixture import GitFixture
from github_command_center.services import GitService

class RecoveryIntegrationTests(unittest.TestCase):
 def setUp(self):self.fx=GitFixture();self.fx.write("a.txt","one\n");self.first=self.fx.commit("first");self.fx.write("a.txt","two\n");self.second=self.fx.commit("second");self.git=GitService(self.fx.path)
 def tearDown(self):self.fx.close()
 def test_safety_branch_preserves_commit(self):self.git.create_safety_branch("gccc-backup/test",self.second);self.assertEqual(self.git.verify_ref("gccc-backup/test"),self.second)
 def test_reflog_contains_previous_head(self):self.fx.run("reset","--hard",self.first);self.assertIn(self.second,self.fx.run("reflog","--format=%H").stdout)
 def test_branch_recovers_previous_commit(self):self.fx.run("reset","--hard",self.first);self.fx.run("branch","recovery/test",self.second);self.assertEqual(self.fx.run("rev-parse","recovery/test").stdout.strip(),self.second)
