from __future__ import annotations
import ast, json, platform, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PKG=ROOT/'github_command_center'; OUT=ROOT/'release-evidence';OUT.mkdir(exist_ok=True)
files=list(PKG.rglob('*.py'));metrics={'version':'3.79.0','python':sys.version.split()[0],'platform':platform.platform(),'python_files':len(files),'python_lines':0,'bare_exception_handlers':0,'broad_exception_handlers':0,'shell_true':0}
for p in files:
 s=p.read_text(encoding='utf-8');metrics['python_lines']+=len(s.splitlines());metrics['shell_true']+=s.count('shell=True');t=ast.parse(s)
 for n in ast.walk(t):
  if isinstance(n,ast.ExceptHandler): metrics['bare_exception_handlers']+=n.type is None;metrics['broad_exception_handlers']+=isinstance(n.type,ast.Name) and n.type.id=='Exception'
metrics['passed']=metrics['bare_exception_handlers']==metrics['broad_exception_handlers']==metrics['shell_true']==0
(OUT/'static-audit.json').write_text(json.dumps(metrics,indent=2));print(json.dumps(metrics,indent=2))
