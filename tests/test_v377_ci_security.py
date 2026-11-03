from pathlib import Path
ROOT=Path(__file__).parents[1]
WF=ROOT/'.github/workflows'
def test_required_workflows_exist():
    assert {'ci.yml','codeql.yml','dependency-review.yml','release-security.yml'} <= {p.name for p in WF.glob('*.yml')}
def test_ci_matrix_and_gates():
    t=(WF/'ci.yml').read_text();
    for value in ('ubuntu-latest','windows-latest',"'3.10'","'3.11'","'3.12'","'3.13'",'ruff check','bandit ','pip-audit','--cov-fail-under=70'): assert value in t
def test_codeql_and_dependency_review():
    assert 'github/codeql-action/init@v4' in (WF/'codeql.yml').read_text()
    assert 'fail-on-severity: high' in (WF/'dependency-review.yml').read_text()
def test_release_supply_chain_controls():
    t=(WF/'release-security.yml').read_text();
    for value in ('actions/attest@v4','sbom.cdx.json','sha256sum','security-gate.json'): assert value in t
def test_dependabot_covers_pip_and_actions():
    t=(ROOT/'.github/dependabot.yml').read_text(); assert 'package-ecosystem: pip' in t and 'package-ecosystem: github-actions' in t

def test_workflow_yaml_is_valid():
 import yaml
 for path in WF.glob('*.yml'):
  assert yaml.safe_load(path.read_text(encoding='utf-8')) is not None

def test_action_refs_do_not_use_branches():
 import re
 text='\n'.join(p.read_text() for p in WF.glob('*.yml'))
 assert not re.search(r'uses:\s*[^\s]+@(main|master|develop|dev)\b',text)
