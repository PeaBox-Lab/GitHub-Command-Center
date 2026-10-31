import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class ArchitecturePhase3Tests(unittest.TestCase):
 def test_new_modules_parse(self):
  for p in [ROOT/'github_command_center/centers/sync/push_pull_center.py',ROOT/'github_command_center/centers/backup/bundle_center.py']:ast.parse(p.read_text(encoding='utf-8'))
 def test_palette_has_async_push_pull(self):self.assertIn('AsyncPushPullCenter',(ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8'))
 def test_palette_has_async_bundle(self):self.assertIn('AsyncBundleCenter',(ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8'))
 def test_network_commands_use_jobservice(self):
  text=(ROOT/'github_command_center/centers/sync/push_pull_center.py').read_text(encoding='utf-8');self.assertIn('run_git_async',text);self.assertNotIn('shell=True',text)
 def test_bundle_create_verify_background(self):
  text=(ROOT/'github_command_center/centers/backup/bundle_center.py').read_text(encoding='utf-8');self.assertIn('self.panel.start(["git", "bundle", "create"',text);self.assertIn('self.panel.start(["git", "bundle", "verify"',text)
