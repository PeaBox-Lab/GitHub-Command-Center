import unittest
from github_command_center.services.release_policy import evaluate_release
class ReleasePolicyTests(unittest.TestCase):
 def test_required_pass(self):self.assertTrue(evaluate_release(tests_ok=True,architecture_ok=True,windows_validation=True,ui_regression=True,package_smoke=True)[0])
 def test_windows_ui_required(self):self.assertFalse(evaluate_release(tests_ok=True,architecture_ok=True,windows_validation=True,ui_regression=False,package_smoke=True)[0])
 def test_signing_optional(self):self.assertTrue(evaluate_release(tests_ok=True,architecture_ok=True,windows_validation=True,ui_regression=True,package_smoke=True,signed=False)[0])
