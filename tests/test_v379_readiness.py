import json,tomllib
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_version_consistency():
 p=tomllib.loads((ROOT/'pyproject.toml').read_text());assert p['project']['version']=='3.81.0';assert '__version__ = "3.81.0"' in (ROOT/'github_command_center/__init__.py').read_text()
def test_strict_architecture_gate():
 s=(ROOT/'scripts/architecture_gate.py').read_text();
 for x in ('shell_lines','domain_modules','largest_domain_lines','largest_domain_classes','direct_domain_subprocess_calls'):assert x in s
 assert "'legacy_lines'" not in s
def test_release_readiness_gate_exists(): assert (ROOT/'scripts/release_readiness_gate.py').exists()
def test_packaging_version_is_derived():
 s=(ROOT/'scripts/packaging_gate.py').read_text();assert 'project_version()' in s
