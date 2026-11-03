import tomllib
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_package_metadata():
 p=tomllib.loads((ROOT/'pyproject.toml').read_text()); assert p['project']['version']=='3.80.0'; assert p['project']['requires-python']=='>=3.10'; assert p['project']['scripts']['github-command-center']=='github_command_center.app:main'
def test_build_system():
 p=tomllib.loads((ROOT/'pyproject.toml').read_text()); assert p['build-system']['build-backend']=='setuptools.build_meta'
def test_packaging_gate_has_self_inclusion_protection():
 s=(ROOT/'scripts/packaging_gate.py').read_text(); assert 'if rel.name.startswith(NAME)' in s; assert "any(n.startswith('dist/')" in s
def test_coverage_is_scoped_and_gated():
 p=tomllib.loads((ROOT/'pyproject.toml').read_text()); assert p['tool']['coverage']['report']['fail_under']==70; assert 'github_command_center/features/domains/*' in p['tool']['coverage']['run']['omit']
