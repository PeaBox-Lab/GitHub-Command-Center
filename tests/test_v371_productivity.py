import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class V371ProductivityTests(unittest.TestCase):
 def source(self):return (ROOT/'github_command_center/centers/git_productivity/productivity.py').read_text(encoding='utf-8')
 def test_parses(self):ast.parse(self.source())
 def test_centers(self):
  for name in ('GitLogVisualizerCenter','StashWorkbenchCenter','WorktreeWorkbenchCenter'):self.assertIn('class '+name,self.source())
 def test_mutations_use_jobs(self):self.assertIn('JobPanel',self.source());self.assertIn('self.panel.start',self.source())
 def test_no_shell_true(self):self.assertNotIn('shell=True',self.source())
 def test_palette_routes(self):
  s=(ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8')
  for n in ('GitLogVisualizerCenter','StashWorkbenchCenter','WorktreeWorkbenchCenter'):self.assertIn(n,s)
 def test_docs_updated(self):
  for name in ('README.md','CHANGELOG.md','RELEASE_NOTES.md','USER_GUIDE.md'):self.assertIn('3.71',(ROOT/name).read_text(encoding='utf-8'))
