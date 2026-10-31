import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class ArchitecturePhase2Tests(unittest.TestCase):
 def test_new_domain_modules_parse(self):
  for folder in ('branches','recovery','release'):
   for p in (ROOT/'github_command_center/centers'/folder).glob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
 def test_palette_routes_extracted_centers(self):
  s=(ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8')
  for name in ('BranchDashboardV2','RecoveryDashboardV2','ReleaseEvidenceV2'):self.assertIn('lambda:'+name,s)
 def test_release_fsck_is_background(self):self.assertIn('self.panel.start(["git","fsck"',(ROOT/'github_command_center/centers/release/evidence.py').read_text(encoding='utf-8'))
 def test_extracted_domains_use_gitservice(self):
  text=''.join(p.read_text(encoding='utf-8') for f in ('branches','recovery','release') for p in (ROOT/'github_command_center/centers'/f).glob('*.py'));self.assertIn('GitService',text);self.assertNotIn('shell=True',text)
