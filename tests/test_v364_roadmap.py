import ast,unittest
from pathlib import Path
ROOT=Path(__file__).parents[1]
class V364RoadmapTests(unittest.TestCase):
 def test_new_centers_parse(self):
  for p in [ROOT/'github_command_center/centers/home/dashboard.py',ROOT/'github_command_center/centers/search/universal_search.py',ROOT/'github_command_center/centers/insights/repository_insights.py',ROOT/'github_command_center/centers/automation/automation_center.py']:ast.parse(p.read_text(encoding='utf-8'))
 def test_palette_has_roadmap_centers(self):
  s=(ROOT/'github_command_center/local_git_gui.py').read_text()
  for x in ('HomeDashboard','UniversalSearchCenter','RepositoryInsightsCenter','AutomationCenter'):self.assertIn(x,s)
 def test_automation_no_shell(self):self.assertNotIn('shell=True',(ROOT/'github_command_center/centers/automation/automation_center.py').read_text())
 def test_legacy_bodies_retired(self):
  t=ast.parse((ROOT/'github_command_center/local_git_gui.py').read_text());c={n.name for n in t.body if isinstance(n,ast.ClassDef)};self.assertFalse(c & {'RepositoryAuditPackCenter','RepositoryLocatorCenter','ChangeStatisticsCenter','GitLogQueryCenter'})
