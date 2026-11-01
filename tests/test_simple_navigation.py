import unittest
from github_command_center.ui.simple_navigation import SIMPLE_MENU,find_destination,primary_menu_names
class SimpleNavigationTests(unittest.TestCase):
 def test_nine_clear_groups(self):self.assertEqual(len(SIMPLE_MENU),9)
 def test_unique_names(self):self.assertEqual(len(primary_menu_names()),len(set(primary_menu_names())))
 def test_daily_tools_have_destination(self):
  for name in ('Changes Center V2','History Center V2','Push & Pull Center','Review Center V2','Release Publish Center V2'):self.assertNotEqual(find_destination(name),'Advanced')
 def test_each_group_small(self):self.assertTrue(all(len(x.primary)<=3 for x in SIMPLE_MENU))
