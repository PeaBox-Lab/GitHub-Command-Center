import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class AsyncMigrationTests(unittest.TestCase):
 def test_modules_parse(self):
  for p in (ROOT/'github_command_center/centers/sync').glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 def test_palette_uses_async_fetch(self):self.assertIn('lambda:AsyncFetchCenter', (ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8'))
 def test_palette_uses_async_prune(self):self.assertIn('lambda:AsyncRemotePruneCenter', (ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8'))
 def test_palette_uses_async_maintenance(self):self.assertIn('lambda:AsyncMaintenanceCenter', (ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8'))
 def test_job_panel_used_by_base(self):self.assertIn('JobPanel', (ROOT/'github_command_center/centers/sync/base.py').read_text(encoding='utf-8'))
 def test_background_git_argument_arrays(self):
  text=''.join(p.read_text(encoding='utf-8') for p in (ROOT/'github_command_center/centers/sync').glob('*.py'));self.assertNotIn('shell=True',text);self.assertIn('run_git_async',text)
