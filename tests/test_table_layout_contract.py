import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class TableLayoutContractTests(unittest.TestCase):
 def source(self):return (ROOT/'github_command_center/ui/table_layout.py').read_text(encoding='utf-8')
 def test_module_parses(self):ast.parse(self.source())
 def test_normalizes_newlines(self):self.assertIn('splitlines()',self.source())
 def test_normalizes_tabs(self):self.assertIn('replace("\\t", "    ")',self.source())
 def test_global_insert_guard(self):self.assertIn('ttk.Treeview.insert = insert',self.source())
 def test_heading_guard(self):self.assertIn('ttk.Treeview.heading = heading',self.source())
 def test_scrollbar_support(self):self.assertIn('ensure_horizontal_scrollbar',self.source())
 def test_width_cap(self):self.assertIn('MAX_WIDTH = 560',self.source())
