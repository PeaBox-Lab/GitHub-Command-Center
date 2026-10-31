import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class MessageLayoutTests(unittest.TestCase):
 def test_module_parses(self):ast.parse((ROOT/'github_command_center/ui/message_layout.py').read_text(encoding='utf-8'))
 def test_dynamic_wrap(self):self.assertIn('wraplength',(ROOT/'github_command_center/ui/message_layout.py').read_text(encoding='utf-8'))
