import unittest
from github_command_center.services.recovery_policy import choose_recovery
class RecoveryPolicyTests(unittest.TestCase):
 def test_reflog_preferred(self):self.assertEqual(choose_recovery(reflog_available=True,commit_known=True,fsck_candidate=True).method,"reflog_branch")
 def test_known_commit(self):self.assertEqual(choose_recovery(reflog_available=False,commit_known=True,fsck_candidate=True).method,"direct_branch")
 def test_fsck(self):self.assertEqual(choose_recovery(reflog_available=False,commit_known=False,fsck_candidate=True).method,"fsck_branch")
 def test_backup_fallback(self):self.assertEqual(choose_recovery(reflog_available=False,commit_known=False,fsck_candidate=False).method,"bundle_or_backup")
 def test_all_paths_non_destructive(self):
  for values in ((1,1,1),(0,1,1),(0,0,1),(0,0,0)):self.assertFalse(choose_recovery(reflog_available=bool(values[0]),commit_known=bool(values[1]),fsck_candidate=bool(values[2])).destructive)
