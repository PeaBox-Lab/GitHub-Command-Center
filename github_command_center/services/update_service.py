from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from pathlib import Path
from .update_policy import assess_update

@dataclass(slots=True)
class ReleaseMetadata:
    version:str
    notes_url:str
    installer_url:str
    sha256:str
    signature_url:str=""

class UpdateService:
    """Offline-verifiable update metadata and downloaded-artifact validation."""
    @staticmethod
    def load_metadata(path:str|Path)->ReleaseMetadata:
        v=json.loads(Path(path).read_text(encoding="utf-8"));return ReleaseMetadata(str(v["version"]),str(v.get("notes_url","")),str(v["installer_url"]),str(v["sha256"]).lower(),str(v.get("signature_url","")))
    @staticmethod
    def is_allowed(current:str,metadata:ReleaseMetadata):return assess_update(current,metadata.version)
    @staticmethod
    def sha256(path:str|Path)->str:
        h=hashlib.sha256()
        with Path(path).open("rb") as f:
            for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
        return h.hexdigest()
    @staticmethod
    def verify(path:str|Path,metadata:ReleaseMetadata)->bool:return UpdateService.sha256(path)==metadata.sha256
