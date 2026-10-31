import unittest
from github_command_center.services.plugin_security import PluginManifest,PluginSecurityService
class PluginSecurityMoreTests(unittest.TestCase):
 def m(self,**x):
  v={"id":"abc.safe","name":"A","version":"1.0.0","command":["git","status"],"permissions":["process.execute"]};v.update(x);return PluginManifest.from_dict(v)
 def test_manifest_version(self):self.assertFalse(PluginSecurityService().assess(self.m(manifest_version=2)).allowed)
 def test_empty_name(self):self.assertFalse(PluginSecurityService().assess(self.m(name="")).allowed)
 def test_empty_command(self):self.assertFalse(PluginSecurityService().assess(self.m(command=[])).allowed)
 def test_custom_allowlist(self):self.assertTrue(PluginSecurityService(["custom"]).assess(self.m(command=["custom","x"])).allowed)
 def test_signature_wrong_manifest(self):
  m=self.m();m.signature=PluginSecurityService.sign_hmac(m,b"x");m.name="changed";self.assertFalse(PluginSecurityService.verify_hmac(m,b"x"))
