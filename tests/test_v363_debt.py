import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1];P=ROOT/'github_command_center/local_git_gui.py'
class V363DebtTests(unittest.TestCase):
 def setUp(self):self.s=P.read_text(encoding='utf-8');self.t=ast.parse(self.s)
 def test_sync_and_release_policy_bodies_retired(self):
  names={n.name for n in self.t.body if isinstance(n,ast.ClassDef)};self.assertNotIn('SyncCenter',names);self.assertNotIn('ReleasePolicyCenter',names)
 def test_aliases_preserve_functionality(self):self.assertIn('SyncCenter = AsyncPushPullCenter',self.s);self.assertIn('ReleasePolicyCenter = PublicReleaseReadinessCenter',self.s)
 def test_line_budget_reduced(self):self.assertLessEqual(len(self.s.splitlines()),5150)
 def test_class_budget_reduced(self):self.assertLessEqual(sum(isinstance(n,ast.ClassDef) for n in self.t.body),143)
