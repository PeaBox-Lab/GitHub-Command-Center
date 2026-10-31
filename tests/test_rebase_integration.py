import unittest
from tests.git_fixture import GitFixture

class RebaseIntegrationTests(unittest.TestCase):
 def setUp(self):self.fx=GitFixture();self.fx.write("a.txt","base\n");self.base=self.fx.commit("base")
 def tearDown(self):self.fx.close()
 def test_clean_rebase(self):
  self.fx.run("switch","-q","-c","feature");self.fx.write("f.txt","feature\n");self.fx.commit("feature");self.fx.run("switch","-q","main");self.fx.write("m.txt","main\n");self.fx.commit("main");self.fx.run("switch","-q","feature");r=self.fx.run("rebase","main",check=False);self.assertEqual(r.returncode,0);self.assertTrue((self.fx.path/"m.txt").exists())
 def test_rebase_abort_restores_branch(self):
  self.fx.run("switch","-q","-c","feature");self.fx.write("a.txt","feature\n");old=self.fx.commit("feature");self.fx.run("switch","-q","main");self.fx.write("a.txt","main\n");self.fx.commit("main");self.fx.run("switch","-q","feature");r=self.fx.run("rebase","main",check=False);self.assertNotEqual(r.returncode,0);self.fx.run("rebase","--abort");self.assertEqual(self.fx.run("rev-parse","HEAD").stdout.strip(),old)
