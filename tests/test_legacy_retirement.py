import ast,re,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1];PATH=ROOT/'github_command_center/local_git_gui.py'
class LegacyRetirementTests(unittest.TestCase):
 def setUp(self):self.text=PATH.read_text(encoding='utf-8');self.tree=ast.parse(self.text)
 def test_retired_class_bodies_absent(self):
  retired={'ReleaseCenter','PullRequestCenter','ActionsCenter','SecurityCenter','CommitInspector','ReflogRecoveryCenter','MaintenanceCenter','PreflightCenter','LocalBranchDashboard','RemotePruneAuditCenter','GitFetchPreviewCenter','BranchProtectionAdvisor'}
  classes={n.name for n in self.tree.body if isinstance(n,ast.ClassDef)};self.assertFalse(retired & classes)
 def test_compatibility_aliases_present(self):
  for name in ('ReleaseCenter','PullRequestCenter','ActionsCenter','SecurityCenter','CommitInspector','ReflogRecoveryCenter','MaintenanceCenter','PreflightCenter','LocalBranchDashboard','RemotePruneAuditCenter','GitFetchPreviewCenter','BranchProtectionAdvisor'):self.assertTrue(any(line.startswith(name+' =') for line in self.text.splitlines()),name)
 def test_sync_gh_calls_reduced(self):self.assertLessEqual(len(re.findall(r'subprocess\.run\(\["gh"',self.text)),1)
 def test_legacy_line_budget(self):self.assertLessEqual(len(self.text.splitlines()),5150)
 def test_shell_true_zero(self):self.assertNotRegex(self.text,r'shell\s*=\s*True')
