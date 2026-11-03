from __future__ import annotations
import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/'github_command_center/local_git_gui.py',ROOT/'github_command_center/core/command_gateway.py',*(ROOT/'github_command_center/features/domains').glob('*.py')]
modules={}
for p in files:
 if p.name=='__init__.py': continue
 text=p.read_text(encoding='utf-8'); tree=ast.parse(text); modules[str(p.relative_to(ROOT))]={'lines':len(text.splitlines()),'classes':sum(isinstance(n,ast.ClassDef) for n in tree.body)}
report={'version':'3.74.0','architecture':'shell + command gateway + bounded Git feature domains','modules':modules,'domain_modules':sum('/domains/' in '/'+k for k in modules),'total_feature_classes':sum(v['classes'] for k,v in modules.items() if '/domains/' in '/'+k),'compatibility_facades':3,'compatibility_exports':True}
(ROOT/'architecture-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
