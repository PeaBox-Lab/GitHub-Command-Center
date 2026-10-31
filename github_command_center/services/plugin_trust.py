from __future__ import annotations

import json
from pathlib import Path


class PluginTrustStore:
    """Local trusted-publisher store. Trust decisions are never inferred automatically."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or Path.home() / ".gccc-plugin-trust.json")

    def load(self) -> dict:
        if not self.path.exists():
            return {"publishers": [], "require_signature": False}
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            publishers = sorted(set(map(str, value.get("publishers", []))))
            return {"publishers": publishers, "require_signature": bool(value.get("require_signature", False))}
        except (OSError, ValueError, TypeError):
            return {"publishers": [], "require_signature": False}

    def save(self, publishers, require_signature=False) -> dict:
        value = {"publishers": sorted(set(map(str, publishers))), "require_signature": bool(require_signature)}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(json.dumps(value, indent=2), encoding="utf-8")
        temp.replace(self.path)
        return value
