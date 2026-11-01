import ast,unittest
from pathlib import Path
from github_command_center.ui.simple_navigation import SIMPLE_MENU,destinations,find_destination
from github_command_center.ui.usability_policy import evaluate_navigation
ROOT=Path(__file__).parents[1]
class UIUsabilityV363Tests(unittest.TestCase):
 def test_navigation_policy_passes(self):self.assertEqual(evaluate_navigation(SIMPLE_MENU),[])
 def test_exactly_nine_groups(self):self.assertEqual(len(SIMPLE_MENU),9)
 def test_three_actions_max(self):self.assertTrue(all(1+len(g.secondary)<=3 for g in SIMPLE_MENU))
 def test_user_facing_labels_not_v2(self):
  for g in SIMPLE_MENU:
   for i in (g.primary,*g.secondary):self.assertNotIn('V2',i.label)
 def test_every_action_has_hint(self):self.assertTrue(all(i.hint.strip() for g in SIMPLE_MENU for i in (g.primary,*g.secondary)))
 def test_destinations_unique(self):self.assertEqual(len(destinations()),len(set(destinations())))
 def test_core_destinations_grouped(self):
  expected={'Changes Center V2':'Changes','History Center V2':'History','Push & Pull Center':'Sync','Review Center V2':'Review','GitHub Network Center':'GitHub','Release Publish Center V2':'Release','Reflog Recovery':'Recover'}
  for dest,group in expected.items():self.assertEqual(find_destination(dest),group)
 def test_ui_regression_script_parses(self):ast.parse((ROOT/'scripts/ui_regression.py').read_text(encoding='utf-8'))
