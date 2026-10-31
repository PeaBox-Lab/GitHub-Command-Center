import unittest
from github_command_center.ui.accessibility_model import AccessibilityPreferences,accessible_palette
class AccessibilityTests(unittest.TestCase):
 def test_defaults(self):self.assertTrue(AccessibilityPreferences().focus_indicators);self.assertFalse(AccessibilityPreferences().high_contrast)
 def test_high_contrast_palette(self):
  p=accessible_palette(True);self.assertEqual(p["bg"],"#000000");self.assertEqual(p["fg"],"#ffffff");self.assertNotEqual(p["accent"],p["bg"])
 def test_normal_palette(self):self.assertEqual(accessible_palette(False)["bg"],"#ffffff")
