from __future__ import annotations
import tomllib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def project_version():
    return tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
def artifact_stem(): return f'github_command_center_python_v{project_version()}'
