from __future__ import annotations
import ast,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; shell=ROOT/'github_command_center/local_git_gui.py'; dom=ROOT/'github_command_center/features/domains'
domains=[p for p in sorted(dom.glob('*.py')) if p.name!='__init__.py']
def metric(p):
 t=p.read_text(encoding='utf-8'); a=ast.parse(t); return {'lines':len(t.splitlines()),'classes':sum(isinstance(n,ast.ClassDef) for n in a.body)}
sm=metric(shell); dm={p.name:metric(p) for p in domains}; domain_text='\n'.join(p.read_text(encoding='utf-8') for p in domains)
facades=[ROOT/'github_command_center/features'/n for n in ('workspace_tools.py','repository_tools.py','expert_tools.py')]
metrics={'shell_lines':sm['lines'],'shell_classes':sm['classes'],'domain_modules':len(domains),'largest_domain_lines':max(v['lines'] for v in dm.values()),'largest_domain_classes':max(v['classes'] for v in dm.values()),'largest_facade_lines':max(len(p.read_text().splitlines()) for p in facades),'direct_domain_subprocess_calls':len(re.findall(r'subprocess\.(?:run|Popen)\s*\(',domain_text)),'shell_true':len(re.findall(r'shell\s*=\s*True',domain_text))}
limits={'shell_lines':300,'shell_classes':1,'domain_modules':18,'largest_domain_lines':600,'largest_domain_classes':10,'largest_facade_lines':20,'direct_domain_subprocess_calls':0,'shell_true':0}
f=[]
for k,v in limits.items():
 if k=='domain_modules':
  if metrics[k]!=v:f.append(f'{k}: {metrics[k]} != {v}')
 elif metrics[k]>v:f.append(f'{k}: {metrics[k]} > {v}')
report={'version':'3.75.0','architecture':'focused shell + Git command gateway + process gateway + compatibility facades + bounded domains','metrics':metrics,'modules':dm,'limits':limits,'passed':not f,'failures':f}
(ROOT/'architecture-gate.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));sys.exit(bool(f))
