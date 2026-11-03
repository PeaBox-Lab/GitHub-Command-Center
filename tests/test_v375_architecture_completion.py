import ast
from pathlib import Path
ROOT=Path(__file__).parents[1]
DOMAINS=ROOT/'github_command_center/features/domains'

def test_no_direct_subprocess_execution_in_domains():
 for path in DOMAINS.glob('*.py'):
  text=path.read_text(encoding='utf-8')
  assert 'subprocess.run(' not in text, path
  assert 'subprocess.Popen(' not in text, path

def test_process_boundary_exists():
 text=(ROOT/'github_command_center/core/process_gateway.py').read_text(encoding='utf-8')
 assert 'def run_process(' in text
 assert 'def start_process(' in text

def test_domain_complexity_budget():
 for path in DOMAINS.glob('*.py'):
  if path.name=='__init__.py': continue
  text=path.read_text(encoding='utf-8'); tree=ast.parse(text)
  assert len(text.splitlines()) <= 600
  assert sum(isinstance(n,ast.ClassDef) for n in tree.body) <= 10

def test_facades_are_compatibility_only():
 for name in ('workspace_tools.py','repository_tools.py','expert_tools.py'):
  text=(ROOT/'github_command_center/features'/name).read_text(encoding='utf-8')
  assert len(text.splitlines()) < 20
  assert 'class ' not in text
