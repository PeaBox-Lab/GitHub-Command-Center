import ast
from pathlib import Path
ROOT=Path(__file__).parents[1]
DOMAINS=ROOT/'github_command_center/features/domains'

def test_eighteen_bounded_domains():
 paths=sorted(p for p in DOMAINS.glob('*.py') if p.name!='__init__.py')
 assert len(paths)==18
 for path in paths:
  text=path.read_text(encoding='utf-8'); tree=ast.parse(text)
  assert len(text.splitlines()) <= 600, path
  assert sum(isinstance(n,ast.ClassDef) for n in tree.body) <= 10, path

def test_facades_remain_small_and_compatible():
 for name in ('workspace_tools.py','repository_tools.py','expert_tools.py'):
  text=(ROOT/'github_command_center/features'/name).read_text(encoding='utf-8')
  assert len(text.splitlines()) < 20
  assert '.domains.' in text

def test_domains_use_command_gateway():
 for path in DOMAINS.glob('*.py'):
  if path.name!='__init__.py': assert 'core.command_gateway import GitError, git' in path.read_text(encoding='utf-8')

def test_no_shell_execution_in_feature_domains():
 text='\n'.join(p.read_text(encoding='utf-8') for p in DOMAINS.glob('*.py'))
 assert 'shell=True' not in text.replace(' ','')
