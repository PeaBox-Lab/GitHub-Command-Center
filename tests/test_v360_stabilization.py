import ast,hashlib,json,tempfile,unittest
from pathlib import Path
from github_command_center.services.update_service import UpdateService
ROOT=Path(__file__).parents[1]
class V360Tests(unittest.TestCase):
 def test_async_center_module_parses(self):ast.parse((ROOT/'github_command_center/centers/sync/submodule_lfs_clone.py').read_text(encoding='utf-8'))
 def test_new_centers_job_based(self):
  s=(ROOT/'github_command_center/centers/sync/submodule_lfs_clone.py').read_text(encoding='utf-8');self.assertIn('run_git_async',s);self.assertIn('JobPanel',s);self.assertNotIn('shell=True',s)
 def test_signature_script_exists(self):self.assertTrue((ROOT/'scripts/verify_windows_signature.ps1').exists())
 def test_update_metadata_roundtrip(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'setup.exe';f.write_bytes(b'abc');m=Path(d)/'m.json';m.write_text(json.dumps({'version':'3.61.0','installer_url':'https://example/setup.exe','sha256':hashlib.sha256(b'abc').hexdigest()}));meta=UpdateService.load_metadata(m);self.assertTrue(UpdateService.verify(f,meta));self.assertTrue(UpdateService.is_allowed('3.60.0',meta).allowed)
 def test_bad_update_hash(self):
  with tempfile.TemporaryDirectory() as d:
   f=Path(d)/'x';f.write_bytes(b'x');m=Path(d)/'m.json';m.write_text(json.dumps({'version':'3.61.0','installer_url':'x','sha256':'0'*64}));self.assertFalse(UpdateService.verify(f,UpdateService.load_metadata(m)))
