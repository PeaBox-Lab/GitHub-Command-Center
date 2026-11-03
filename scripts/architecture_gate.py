from __future__ import annotations
import ast,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
shell=ROOT/'github_command_center/local_git_gui.py';domains=sorted(p for p in (ROOT/'github_command_center/features/domains').glob('*.py') if p.name!='__init__.py')
facades=[ROOT/'github_command_center/features'/n for n in ('workspace_tools.py','repository_tools.py','expert_tools.py')]
def metric(p):
 s=p.read_text(encoding='utf-8');t=ast.parse(s);return {'lines':len(s.splitlines()),'classes':sum(isinstance(n,ast.ClassDef) for n in t.body)}
sm=metric(shell);dm={p.name:metric(p) for p in domains};all_domain='\n'.join(p.read_text(encoding='utf-8') for p in domains)
metrics={'shell_lines':sm['lines'],'shell_classes':sm['classes'],'domain_modules':len(domains),'largest_domain_lines':max(v['lines'] for v in dm.values()),'largest_domain_classes':max(v['classes'] for v in dm.values()),'largest_facade_lines':max(len(p.read_text().splitlines()) for p in facades),'direct_domain_subprocess_calls':len(re.findall(r'subprocess\.(?:run|Popen)\s*\(',all_domain)),'shell_true':len(re.findall(r'shell\s*=\s*True',all_domain))}
limits={'shell_lines':300,'shell_classes':1,'domain_modules':18,'largest_domain_lines':600,'largest_domain_classes':10,'largest_facade_lines':20,'direct_domain_subprocess_calls':0,'shell_true':0}
fail=[]
for k,v in limits.items():
 if k=='domain_modules':
  if metrics[k]!=v:fail.append(f'{k}: {metrics[k]} != {v}')
 elif metrics[k]>v:fail.append(f'{k}: {metrics[k]} > {v}')
report={'version':'3.79.0','metrics':metrics,'limits':limits,'passed':not fail,'failures':fail,'modules':dm}
(ROOT/'architecture-gate.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(bool(fail))
