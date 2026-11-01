import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1];P=ROOT/'github_command_center/local_git_gui.py'
class DebtTests(unittest.TestCase):
 def setUp(self):self.s=P.read_text(encoding='utf-8');self.t=ast.parse(self.s)
 def test_retired_bodies_absent(self):
  retired={'SubmoduleCenter','LFSCenter','CloneWizard','BundleInspector','ReleaseEvidenceCenter','ChangeReviewCenter','GitMaintenanceScheduleCenter','CommitGraphMaintenanceCenter'};classes={n.name for n in self.t.body if isinstance(n,ast.ClassDef)};self.assertFalse(classes&retired)
 def test_compat_aliases(self):
  for name in ('SubmoduleCenter','LFSCenter','CloneWizard','BundleInspector','ReleaseEvidenceCenter','ChangeReviewCenter','GitMaintenanceScheduleCenter','CommitGraphMaintenanceCenter'):self.assertIn(name+' =',self.s)
 def test_lower_line_budget(self):self.assertLessEqual(len(self.s.splitlines()),5225)
 def test_lower_class_budget(self):self.assertLessEqual(sum(isinstance(n,ast.ClassDef) for n in self.t.body),145)
