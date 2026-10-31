import unittest
from github_command_center.services.update_policy import assess_update,parse_version
class UpdatePolicyTests(unittest.TestCase):
 def test_parse(self):self.assertEqual(parse_version("v3.50.0"),(3,50,0))
 def test_invalid(self):
  with self.assertRaises(ValueError):parse_version("3.50")
 def test_newer_allowed(self):self.assertTrue(assess_update("3.49.0","3.50.0").allowed)
 def test_same_blocked(self):self.assertFalse(assess_update("3.50.0","3.50.0").allowed)
 def test_older_blocked(self):self.assertFalse(assess_update("3.50.0","3.49.9").allowed)
 def test_major_blocked(self):self.assertFalse(assess_update("3.50.0","4.0.0").allowed)
 def test_major_opt_in(self):self.assertTrue(assess_update("3.50.0","4.0.0",allow_major=True).allowed)
