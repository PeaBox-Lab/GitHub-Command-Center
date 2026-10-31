import unittest
from github_command_center.services.safety_policy import assess_branch_delete,assess_history_rewrite

class SafetyPolicyTests(unittest.TestCase):
    def test_safe_delete(self):self.assertTrue(assess_branch_delete(current=False,worktree_active=False,merged=True,ahead=0).allowed)
    def test_current_branch_blocked(self):self.assertFalse(assess_branch_delete(current=True,worktree_active=False,merged=True,ahead=0).allowed)
    def test_worktree_branch_blocked(self):self.assertFalse(assess_branch_delete(current=False,worktree_active=True,merged=True,ahead=0).allowed)
    def test_unmerged_branch_blocked(self):self.assertFalse(assess_branch_delete(current=False,worktree_active=False,merged=False,ahead=0).allowed)
    def test_ahead_branch_blocked(self):self.assertFalse(assess_branch_delete(current=False,worktree_active=False,merged=True,ahead=2).allowed)
    def test_rewrite_requires_clean(self):self.assertFalse(assess_history_rewrite(clean=False,detached=False,protected_branch=False).allowed)
    def test_rewrite_blocks_detached(self):self.assertFalse(assess_history_rewrite(clean=True,detached=True,protected_branch=False).allowed)
    def test_protected_warning(self):
        result=assess_history_rewrite(clean=True,detached=False,protected_branch=True);self.assertTrue(result.allowed);self.assertTrue(result.warnings)
if __name__=="__main__":unittest.main()
