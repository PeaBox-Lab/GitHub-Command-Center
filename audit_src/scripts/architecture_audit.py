from __future__ import annotations
import ast, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/'github_command_center/local_git_gui.py',*(ROOT/'github_command_center/features').glob('*_tools.py'),ROOT/'github_command_center/core/command_gateway.py']
modules={}
for p in files:
 text=p.read_text(encoding='utf-8'); tree=ast.parse(text); modules[str(p.relative_to(ROOT))]={'lines':len(text.splitlines()),'classes':sum(isinstance(n,ast.ClassDef) for n in tree.body)}
report={'version':'3.73.0','architecture':'shell + command gateway + feature domains','modules':modules,'total_feature_classes':sum(v['classes'] for k,v in modules.items() if '/features/' in '/'+k),'compatibility_exports':True}
(ROOT/'architecture-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2))
