from __future__ import annotations
import ast, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
paths = [ROOT/'github_command_center/local_git_gui.py', *(ROOT/'github_command_center/features').glob('*_tools.py')]
def metrics_for(path):
    text=path.read_text(encoding='utf-8'); tree=ast.parse(text)
    return {'lines':len(text.splitlines()),'classes':sum(isinstance(n,ast.ClassDef) for n in tree.body)}
shell=metrics_for(paths[0]); features={p.name:metrics_for(p) for p in paths[1:]}
all_text='\n'.join(p.read_text(encoding='utf-8') for p in paths)
metrics={'shell_lines':shell['lines'],'shell_classes':shell['classes'],'largest_feature_module_lines':max(v['lines'] for v in features.values()),'feature_modules':len(features),'shell_true':len(re.findall(r'shell\s*=\s*True',all_text))}
limits={'shell_lines':300,'shell_classes':1,'largest_feature_module_lines':1800,'feature_modules':3,'shell_true':0}
failures=[f'{k}: {metrics[k]} > {limit}' for k,limit in limits.items() if metrics[k]>limit]
report={'version':'3.73.0','metrics':metrics,'modules':features,'limits':limits,'passed':not failures,'failures':failures}
(ROOT/'architecture-gate.json').write_text(json.dumps(report,indent=2),encoding='utf-8'); print(json.dumps(report,indent=2)); sys.exit(1 if failures else 0)
