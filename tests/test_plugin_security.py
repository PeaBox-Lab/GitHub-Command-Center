import json,tempfile,unittest
from pathlib import Path
from github_command_center.services.plugin_security import PluginManifest,PluginSecurityService

class PluginSecurityTests(unittest.TestCase):
 def manifest(self,**updates):
  value={"id":"com.example.safe","name":"Safe","version":"1.2.3","command":["git","status"],"permissions":["process.execute","git.read"],"publisher":"Trusted"};value.update(updates);return PluginManifest.from_dict(value)
 def test_valid_manifest_allowed(self):self.assertTrue(PluginSecurityService().assess(self.manifest(),trusted_publishers=["Trusted"]).allowed)
 def test_bad_id_blocked(self):self.assertFalse(PluginSecurityService().assess(self.manifest(id="BAD ID")).allowed)
 def test_bad_version_blocked(self):self.assertFalse(PluginSecurityService().assess(self.manifest(version="one")).allowed)
 def test_unknown_permission_blocked(self):self.assertFalse(PluginSecurityService().assess(self.manifest(permissions=["process.execute","root.all"])).allowed)
 def test_missing_execute_permission_blocked(self):self.assertFalse(PluginSecurityService().assess(self.manifest(permissions=["git.read"])).allowed)
 def test_unallowlisted_executable_blocked(self):self.assertFalse(PluginSecurityService().assess(self.manifest(command=["powershell","x"])).allowed)
 def test_unsigned_warning(self):self.assertTrue(PluginSecurityService().assess(self.manifest()).warnings)
 def test_signature_policy_blocks_unsigned(self):self.assertFalse(PluginSecurityService().assess(self.manifest(),require_signature=True).allowed)
 def test_untrusted_publisher_warning(self):self.assertTrue(any("Publisher" in x for x in PluginSecurityService().assess(self.manifest(),trusted_publishers=[]).warnings))
 def test_canonical_payload_stable(self):self.assertEqual(self.manifest().canonical_payload(),self.manifest().canonical_payload())
 def test_digest_and_verify(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x";p.write_bytes(b"abc");h=PluginSecurityService.digest(p);self.assertTrue(PluginSecurityService.verify_file(p,h));self.assertFalse(PluginSecurityService.verify_file(p,"0"*64))
 def test_hmac_roundtrip(self):
  m=self.manifest();sig=PluginSecurityService.sign_hmac(m,b"secret");m.signature=sig;self.assertTrue(PluginSecurityService.verify_hmac(m,b"secret"));self.assertFalse(PluginSecurityService.verify_hmac(m,b"wrong"))
 def test_load_manifest(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"p.json";p.write_text(json.dumps({"id":"com.example.safe","name":"Safe","version":"1.0.0","command":["git","status"],"permissions":["process.execute"]}),encoding="utf-8");self.assertEqual(PluginSecurityService().load(p).plugin_id,"com.example.safe")
