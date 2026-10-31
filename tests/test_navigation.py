import unittest
from github_command_center.ui.navigation import NAVIGATION_SECTIONS,find_items,section_names
class NavigationTests(unittest.TestCase):
 def test_expected_task_sections(self):self.assertEqual(section_names(),("Home","Changes","History","Branches","Sync","Review","GitHub","Release","Recover","Advanced"))
 def test_unique_sections(self):self.assertEqual(len(section_names()),len(set(section_names())))
 def test_every_section_has_items(self):self.assertTrue(all(s.items for s in NAVIGATION_SECTIONS))
 def test_search(self):self.assertIn(("Recover","Reflog Recovery"),find_items("reflog"));self.assertIn(("Changes","Visual Diff"),find_items("side by side"))
