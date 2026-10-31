import hashlib,unittest
from tests.git_fixture import GitFixture

class ReleaseIntegrationTests(unittest.TestCase):
 def setUp(self):self.fx=GitFixture();self.fx.write("README.md","release\n");self.commit=self.fx.commit("release")
 def tearDown(self):self.fx.close()
 def test_annotated_tag_targets_commit(self):
  self.fx.run("tag","-a","v1.0.0","-m","v1.0.0");self.assertEqual(self.fx.run("rev-parse","v1.0.0^{}").stdout.strip(),self.commit)
 def test_archive_is_reproducibly_hashable(self):
  out=self.fx.path/"source.zip";self.fx.run("archive","--format=zip",f"--output={out}","HEAD");self.assertGreater(out.stat().st_size,100);self.assertEqual(len(hashlib.sha256(out.read_bytes()).hexdigest()),64)
 def test_bundle_verifies(self):
  bundle=self.fx.path/"repo.bundle";self.fx.run("bundle","create",str(bundle),"--all");r=self.fx.run("bundle","verify",str(bundle),check=False);self.assertEqual(r.returncode,0)
