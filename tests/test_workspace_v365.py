import ast,tempfile,unittest
from pathlib import Path
from github_command_center.ui.workspace_state import WorkspaceStateService
ROOT=Path(__file__).parents[1]
class WorkspaceV365Tests(unittest.TestCase):
 def test_state(self):
  with tempfile.TemporaryDirectory() as d:
   s=WorkspaceStateService(Path(d)/'w.json');st=s.load();s.record_tool(st,'History');s.record_tool(st,'Changes');s.record_tool(st,'History');self.assertEqual(st.recent_tools[:2],['History','Changes']);s.toggle_favorite(st,'Changes');self.assertIn('Changes',s.load().favorite_tools)
 def test_shell_contract(self):
  x=(ROOT/'github_command_center/ui/workspace_shell.py').read_text(encoding='utf-8');ast.parse(x);self.assertIn('SIMPLE_MENU',x);self.assertIn('Recent tools',x);self.assertIn('Favorites',x)
