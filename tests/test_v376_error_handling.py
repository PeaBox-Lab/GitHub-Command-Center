import ast
from pathlib import Path
ROOT=Path(__file__).parents[1]
PACKAGE=ROOT/'github_command_center'

def counts():
 bare=broad=0
 for path in PACKAGE.rglob('*.py'):
  tree=ast.parse(path.read_text(encoding='utf-8'))
  for node in ast.walk(tree):
   if isinstance(node,ast.ExceptHandler):
    bare += node.type is None
    broad += isinstance(node.type,ast.Name) and node.type.id=='Exception'
 return bare,broad

def test_no_bare_handlers(): assert counts()[0] == 0
def test_no_broad_exception_handlers(): assert counts()[1] == 0
def test_typed_boundary_defined():
 text=(PACKAGE/'core/error_boundary.py').read_text(encoding='utf-8')
 assert 'HANDLED_EXCEPTIONS=' in text and 'report_error' in text
def test_control_flow_exceptions_not_swallowed():
 text=(PACKAGE/'core/error_boundary.py').read_text(encoding='utf-8')
 assert 'BaseException' not in text and 'KeyboardInterrupt' not in text and 'SystemExit' not in text
