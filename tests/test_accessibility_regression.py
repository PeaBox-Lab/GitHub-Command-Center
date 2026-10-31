import ast,unittest
from pathlib import Path
from github_command_center.ui.accessibility_model import AccessibilityPreferences,accessible_palette
ROOT=Path(__file__).parents[1]
class AccessibilityRegressionTests(unittest.TestCase):
 def test_contrast_modes_have_text_and_background_difference(self):
  for mode in (False,True):
   p=accessible_palette(mode);self.assertNotEqual(p["fg"],p["bg"]);self.assertNotEqual(p["selection"],p["bg"])
 def test_preferences_are_immutable(self):
  p=AccessibilityPreferences()
  with self.assertRaises(Exception):p.large_text=True
 def test_center_has_keyboard_help(self):
  text=(ROOT/"github_command_center/centers/accessibility_center.py").read_text(encoding="utf-8");self.assertIn("Ctrl+K",text);self.assertIn("Shift+Tab",text);self.assertIn("Enter / Space",text)
 def test_accessibility_module_parses(self):ast.parse((ROOT/"github_command_center/ui/accessibility.py").read_text(encoding="utf-8"))
 def test_model_has_no_tk_import(self):self.assertNotIn("tkinter",(ROOT/"github_command_center/ui/accessibility_model.py").read_text(encoding="utf-8"))
 def test_document_rule_color_not_alone(self):self.assertIn("Do not use color alone",(ROOT/"ACCESSIBILITY.md").read_text(encoding="utf-8"))
