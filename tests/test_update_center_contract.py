import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class UpdateCenterContractTests(unittest.TestCase):
 def test_module_parses(self):ast.parse((ROOT/'github_command_center/centers/update/update_center.py').read_text(encoding='utf-8'))
 def test_no_auto_installer_execution(self):
  s=(ROOT/'github_command_center/centers/update/update_center.py').read_text(encoding='utf-8');self.assertNotIn('subprocess',s);self.assertIn('never silently installs',s.lower())
