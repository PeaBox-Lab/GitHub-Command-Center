import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class V371IncrementalTests(unittest.TestCase):
 def test_new_centers_parse(self): ast.parse((ROOT/'github_command_center/centers/developer/engineering.py').read_text())
 def test_new_centers_present(self):
  s=(ROOT/'github_command_center/centers/developer/engineering.py').read_text()
  self.assertIn('class RefCompareCenter',s);self.assertIn('class RevisionExplainCenter',s)
 def test_readme_current(self): self.assertIn('v3.71.0',(ROOT/'README.md').read_text())
 def test_docs_current(self):
  for f in ('CHANGELOG.md','RELEASE_NOTES.md','USER_GUIDE.md'):
   self.assertIn('3.71', (ROOT/f).read_text())
 def test_no_shell_true(self):
  text=''.join(p.read_text(errors='ignore') for p in (ROOT/'github_command_center').rglob('*.py'));self.assertNotIn('shell=True',text)
