"""Portable workspace profiles for common repository contexts."""
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass(frozen=True)
class WorkspaceProfile:
    name: str
    repository: str
    branch: str = ""
    note: str = ""

class WorkspaceProfileService:
    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or (Path.home()/".github_command_center")
        self.path = self.config_dir/"workspace_profiles.json"
    def load(self):
        if not self.path.exists(): return []
        try:
            data=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,ValueError,json.JSONDecodeError): return []
        out=[]
        for item in data if isinstance(data,list) else []:
            if isinstance(item,dict) and item.get("name") and item.get("repository"):
                out.append(WorkspaceProfile(str(item["name"]),str(item["repository"]),str(item.get("branch","")),str(item.get("note",""))))
        return out
    def save(self, profiles):
        self.config_dir.mkdir(parents=True,exist_ok=True)
        temp=self.path.with_suffix(".tmp")
        temp.write_text(json.dumps([asdict(p) for p in profiles],indent=2),encoding="utf-8")
        temp.replace(self.path)
    def upsert(self, profile):
        profiles=[p for p in self.load() if p.name.casefold()!=profile.name.casefold()]
        profiles.append(profile); profiles.sort(key=lambda p:p.name.casefold()); self.save(profiles); return profiles
    def remove(self,name):
        profiles=[p for p in self.load() if p.name.casefold()!=name.casefold()]; self.save(profiles); return profiles
    def export_to(self,target): Path(target).write_text(json.dumps([asdict(p) for p in self.load()],indent=2),encoding="utf-8")
    def import_from(self,source):
        data=json.loads(Path(source).read_text(encoding="utf-8")); profiles=[]
        for item in data:
            profiles.append(WorkspaceProfile(str(item["name"]),str(item["repository"]),str(item.get("branch","")),str(item.get("note",""))))
        self.save(profiles); return profiles
