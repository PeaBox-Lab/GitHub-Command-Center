from github_command_center.core.error_boundary import HANDLED_EXCEPTIONS, report_error

import json
import os
from pathlib import Path

APP_DIR = Path(os.getenv("APPDATA") or (Path.home() / ".config")) / "GitHubCommandCenter"
CONFIG_FILE = APP_DIR / "config.json"


def load_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except HANDLED_EXCEPTIONS:
        return {"workspace": str(Path.home() / "GitHub")}


def save_config(config):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")

