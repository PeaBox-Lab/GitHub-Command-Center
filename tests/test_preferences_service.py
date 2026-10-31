import tempfile,unittest
from pathlib import Path
from github_command_center.services import PreferencesService
class PreferencesServiceTests(unittest.TestCase):
    def test_defaults_and_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"preferences.json";s=PreferencesService(p);self.assertEqual(s.load()["default_branch"],"main");s.save({"theme":"alt","history_limit":500});v=s.load();self.assertEqual(v["theme"],"alt");self.assertEqual(v["history_limit"],500);self.assertTrue(v["confirm_destructive"])
    def test_invalid_json_falls_back(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"preferences.json";p.write_text("bad",encoding="utf-8");self.assertEqual(PreferencesService(p).load()["theme"],"clam")
if __name__=="__main__":unittest.main()
