import ast,unittest
from pathlib import Path
R=Path(__file__).parents[1]
class T(unittest.TestCase):
 def test_parse(self):ast.parse((R/'github_command_center/centers/git_productivity/productivity.py').read_text())
 def test_centers(self):
  s=(R/'github_command_center/centers/git_productivity/productivity.py').read_text();self.assertIn('class CommitGraphFilterCenter',s);self.assertIn('class StashConflictPreviewCenter',s);self.assertIn("'merge-tree'",s)
 def test_docs(self):
  for f in ('README.md','CHANGELOG.md','RELEASE_NOTES.md','USER_GUIDE.md'):self.assertIn('3.72',(R/f).read_text())

