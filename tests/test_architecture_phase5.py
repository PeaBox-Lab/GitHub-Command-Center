import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class Phase5Tests(unittest.TestCase):
 def test_modules_parse(self):
  for p in [ROOT/'github_command_center/centers/review/review_center.py',ROOT/'github_command_center/centers/release/publish_center.py',ROOT/'github_command_center/centers/github/workflow_center.py']:ast.parse(p.read_text(encoding='utf-8'))
 def test_palette_routes_new_centers(self):
  s=(ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8')
  for x in ('ReviewCenterV2','ReleasePublishCenterV2','AsyncGitHubWorkflowCenter'):self.assertIn(x,s)
 def test_github_workflows_async(self):
  s=(ROOT/'github_command_center/centers/github/workflow_center.py').read_text();self.assertIn('self.panel.start',s);self.assertNotIn('subprocess.run',s)
 def test_release_publish_async(self):
  s=(ROOT/'github_command_center/centers/release/publish_center.py').read_text();self.assertIn('["gh","release","create"',s.replace(' ',''));self.assertIn('JobPanel',s)
 def test_review_quality_async(self):self.assertIn('JobPanel',(ROOT/'github_command_center/centers/review/review_center.py').read_text())
