from __future__ import annotations
from dataclasses import asdict,dataclass
from pathlib import Path
import json
from .git_service import GitService

@dataclass(slots=True)
class HealthSnapshot:
    branch:str
    head:str
    clean:bool
    changed:int
    upstream:str
    ahead:int|None
    behind:int|None
    object_status:str

class HealthSnapshotService:
    def __init__(self,repo):self.repo=Path(repo).resolve();self.git=GitService(self.repo)
    def capture(self):
        s=self.git.repository_state();objects=self.git.execute('count-objects','-vH',check=False).output
        return HealthSnapshot(s.branch,s.head,s.clean,len(s.changed_paths),s.upstream,s.ahead,s.behind,objects)
    @staticmethod
    def to_json(snapshot):return json.dumps(asdict(snapshot),indent=2)

