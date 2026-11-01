from __future__ import annotations
import json
from dataclasses import asdict,dataclass,field
from pathlib import Path
@dataclass(slots=True)
class WorkspaceState:
    last_tool:str='Home Dashboard';recent_tools:list[str]=field(default_factory=list);favorite_tools:list[str]=field(default_factory=list);geometry:str='1280x820'
class WorkspaceStateService:
    def __init__(self,path=None):self.path=Path(path or Path.home()/'.gccc-workspace.json')
    def load(self):
        if not self.path.exists():return WorkspaceState()
        try:
            v=json.loads(self.path.read_text(encoding='utf-8'));return WorkspaceState(str(v.get('last_tool','Home Dashboard')),list(v.get('recent_tools',[]))[:12],list(v.get('favorite_tools',[])),str(v.get('geometry','1280x820')))
        except Exception:return WorkspaceState()
    def save(self,s):
        self.path.parent.mkdir(parents=True,exist_ok=True);t=self.path.with_suffix(self.path.suffix+'.tmp');t.write_text(json.dumps(asdict(s),indent=2),encoding='utf-8');t.replace(self.path)
    def record_tool(self,s,name):s.last_tool=name;s.recent_tools=([name]+[x for x in s.recent_tools if x!=name])[:12];self.save(s)
    def toggle_favorite(self,s,name):s.favorite_tools=[x for x in s.favorite_tools if x!=name] if name in s.favorite_tools else [*s.favorite_tools,name];self.save(s)
