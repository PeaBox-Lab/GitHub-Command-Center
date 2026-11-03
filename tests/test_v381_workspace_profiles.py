import json
from pathlib import Path
from github_command_center.services.workspace_profile_service import WorkspaceProfile,WorkspaceProfileService

def test_workspace_profile_crud(tmp_path):
 s=WorkspaceProfileService(tmp_path);p=WorkspaceProfile('Banking','/repo','main','daily');s.upsert(p);assert s.load()==[p];s.upsert(WorkspaceProfile('Banking','/repo2','dev','updated'));rows=s.load();assert len(rows)==1 and rows[0].repository=='/repo2';s.remove('banking');assert s.load()==[]
def test_workspace_profiles_sorted(tmp_path):
 s=WorkspaceProfileService(tmp_path);s.upsert(WorkspaceProfile('Zulu','/z'));s.upsert(WorkspaceProfile('alpha','/a'));assert [p.name for p in s.load()]==['alpha','Zulu']
def test_workspace_import_export(tmp_path):
 s=WorkspaceProfileService(tmp_path/'one');s.upsert(WorkspaceProfile('A','/a','main','x'));target=tmp_path/'profiles.json';s.export_to(target);s2=WorkspaceProfileService(tmp_path/'two');rows=s2.import_from(target);assert rows[0].name=='A' and s2.load()[0].branch=='main'
def test_malformed_storage_is_safe(tmp_path):
 s=WorkspaceProfileService(tmp_path);tmp_path.mkdir(exist_ok=True);s.path.write_text('{broken',encoding='utf-8');assert s.load()==[]
def test_version_v381():
 root=Path(__file__).parents[1];assert '__version__ = "3.81.0"' in (root/'github_command_center/__init__.py').read_text()
