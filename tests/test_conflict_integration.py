import unittest
from tests.git_fixture import GitFixture

class ConflictIntegrationTests(unittest.TestCase):
 def setUp(self):self.fx=GitFixture();self.fx.write("a.txt","base\n");self.fx.commit("base")
 def tearDown(self):self.fx.close()
 def make_conflict(self):
  self.fx.run("switch","-q","-c","feature");self.fx.write("a.txt","feature\n");self.fx.commit("feature");self.fx.run("switch","-q","main");self.fx.write("a.txt","main\n");self.fx.commit("main");return self.fx.run("merge","feature",check=False)
 def test_conflict_has_three_index_stages(self):
  self.assertNotEqual(self.make_conflict().returncode,0);raw=self.fx.run("ls-files","--stage").stdout;self.assertIn(" 1\ta.txt",raw);self.assertIn(" 2\ta.txt",raw);self.assertIn(" 3\ta.txt",raw)
 def test_merge_abort_cleans_conflict_state(self):
  self.make_conflict();self.fx.run("merge","--abort");self.assertEqual(self.fx.run("diff","--name-only","--diff-filter=U").stdout.strip(),"")
 def test_ours_can_be_staged(self):
  self.make_conflict();self.fx.run("checkout","--ours","--","a.txt");self.fx.run("add","a.txt");self.assertEqual(self.fx.run("diff","--name-only","--diff-filter=U").stdout.strip(),"")
