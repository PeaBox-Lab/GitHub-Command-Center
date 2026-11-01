from __future__ import annotations
import ast,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'github_command_center/local_git_gui.py';text=path.read_text(encoding='utf-8');tree=ast.parse(text)
metrics={
 'legacy_lines':len(text.splitlines()),
 'legacy_classes':sum(isinstance(n,ast.ClassDef) for n in tree.body),
 'heavy_sync_calls':len(re.findall(r'git\(self\.repo,"(?:fetch|fsck|gc|maintenance|clone|bundle|submodule|push|pull)',text)),
 'direct_sync_gh_calls':len(re.findall(r'subprocess\.run\(\["gh"',text)),
 'shell_true':len(re.findall(r'shell\s*=\s*True',text)),
}
limits={'legacy_lines':5050,'legacy_classes':139,'heavy_sync_calls':32,'direct_sync_gh_calls':0,'shell_true':0}
failures=[f'{k}: {metrics[k]} > {limit}' for k,limit in limits.items() if metrics[k]>limit]
report={'metrics':metrics,'limits':limits,'passed':not failures,'failures':failures};(ROOT/'architecture-gate.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2));raise SystemExit(0 if not failures else 1)
