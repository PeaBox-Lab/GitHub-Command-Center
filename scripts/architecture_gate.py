from __future__ import annotations
import ast, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
shell=ROOT/'github_command_center/local_git_gui.py'
domains=sorted((ROOT/'github_command_center/features/domains').glob('*.py'))
domains=[p for p in domains if p.name!='__init__.py']
def metric(path):
 text=path.read_text(encoding='utf-8'); tree=ast.parse(text)
 return {'lines':len(text.splitlines()),'classes':sum(isinstance(n,ast.ClassDef) for n in tree.body)}
shell_m=metric(shell); dm={p.name:metric(p) for p in domains}; all_text='\n'.join([shell.read_text(),*[p.read_text() for p in domains]])
metrics={'shell_lines':shell_m['lines'],'shell_classes':shell_m['classes'],'domain_modules':len(domains),'largest_domain_lines':max(v['lines'] for v in dm.values()),'largest_domain_classes':max(v['classes'] for v in dm.values()),'shell_true':len(re.findall(r'shell\s*=\s*True',all_text))}
limits={'shell_lines':300,'shell_classes':1,'domain_modules':18,'largest_domain_lines':600,'largest_domain_classes':10,'shell_true':0}
failures=[]
for k,limit in limits.items():
 if k=='domain_modules':
  if metrics[k]!=limit: failures.append(f'{k}: {metrics[k]} != {limit}')
 elif metrics[k]>limit: failures.append(f'{k}: {metrics[k]} > {limit}')
report={'version':'3.74.0','architecture':'focused shell + command gateway + compatibility facades + bounded feature domains','metrics':metrics,'modules':dm,'limits':limits,'passed':not failures,'failures':failures}
(ROOT/'architecture-gate.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2)); sys.exit(1 if failures else 0)
