import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class V370DeveloperTests(unittest.TestCase):
 def source(self):return (ROOT/'github_command_center/centers/developer/engineering.py').read_text(encoding='utf-8')
 def test_parses(self):ast.parse(self.source())
 def test_centers(self):
  for name in ('DevQualityCenter','CodeSearchCenter','PatchSeriesCenter','RepositoryMetricsCenter','BuildCommandCenter','DevArtifactCenter'):self.assertIn('class '+name,self.source())
 def test_async_quality(self):self.assertIn('JobPanel',self.source());self.assertNotIn('shell=True',self.source())
 def test_monolith_budget(self):self.assertLessEqual(len((ROOT/'github_command_center/local_git_gui.py').read_text(encoding='utf-8').splitlines()),5150)

