import tempfile,unittest
from pathlib import Path
from github_command_center.services.plugin_trust import PluginTrustStore
class PluginTrustTests(unittest.TestCase):
 def test_defaults(self):
  with tempfile.TemporaryDirectory() as d:self.assertEqual(PluginTrustStore(Path(d)/"x.json").load(),{"publishers":[],"require_signature":False})
 def test_roundtrip_and_deduplicate(self):
  with tempfile.TemporaryDirectory() as d:
   s=PluginTrustStore(Path(d)/"x.json");s.save(["B","A","A"],True);self.assertEqual(s.load(),{"publishers":["A","B"],"require_signature":True})
 def test_invalid_json(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/"x.json";p.write_text("bad");self.assertEqual(PluginTrustStore(p).load()["publishers"],[])
