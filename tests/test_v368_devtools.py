import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class V368DevToolsTests(unittest.TestCase):
 def test_module_parses(self):ast.parse((ROOT/'github_command_center/centers/developer/tools.py').read_text(encoding='utf-8'))
 def test_toolbox_present(self):self.assertIn('class DeveloperToolboxCenter',(ROOT/'github_command_center/centers/developer/tools.py').read_text(encoding='utf-8'))
 def test_object_query_present(self):self.assertIn('class GitObjectQueryCenter',(ROOT/'github_command_center/centers/developer/tools.py').read_text(encoding='utf-8'))
 def test_legacy_monolith_did_not_grow(self):self.assertLessEqual(len((ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8').splitlines()),5150)
 def test_no_shell_true(self):self.assertNotIn('shell=True',(ROOT/'github_command_center/centers/developer/tools.py').read_text(encoding='utf-8'))
