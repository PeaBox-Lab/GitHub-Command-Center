import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class Phase4Tests(unittest.TestCase):
 def test_modules_parse(self):
  for p in [ROOT/'github_command_center/centers/changes/changes_center.py',ROOT/'github_command_center/centers/history/history_center.py',ROOT/'github_command_center/centers/github/async_github_center.py',ROOT/'scripts/ui_regression.py']:ast.parse(p.read_text(encoding='utf-8'))
 def test_palette_routes_centers(self):
  s=(ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8')
  for name in ('ChangesCenterV2','HistoryCenterV2','AsyncGitHubCenter'):self.assertIn(name,s)
 def test_github_calls_background(self):
  text=(ROOT/'github_command_center/centers/github/async_github_center.py').read_text(encoding='utf-8');self.assertIn('JobPanel',text);self.assertIn('self.panel.start',text);self.assertNotIn('shell=True',text)
 def test_changes_history_gitservice(self):
  text=(ROOT/'github_command_center/centers/changes/changes_center.py').read_text()+ (ROOT/'github_command_center/centers/history/history_center.py').read_text();self.assertIn('GitService',text);self.assertNotIn('shell=True',text)
