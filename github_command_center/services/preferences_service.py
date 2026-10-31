from __future__ import annotations

import json
from pathlib import Path


DEFAULTS = {
    "theme": "clam",
    "font_size": 9,
    "history_limit": 200,
    "confirm_destructive": True,
    "default_branch": "main",
}


class PreferencesService:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path or Path.home() / ".gccc-preferences.json")

    def load(self) -> dict:
        if not self.path.exists():
            return dict(DEFAULTS)
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            return {**DEFAULTS, **value}
        except (OSError, json.JSONDecodeError):
            return dict(DEFAULTS)

    def save(self, values: dict) -> dict:
        clean = {**DEFAULTS, **values}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(clean, indent=2), encoding="utf-8")
        temporary.replace(self.path)
        return clean
