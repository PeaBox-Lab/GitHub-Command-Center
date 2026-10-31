from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];legacy=ROOT/'github_command_center/local_git_gui.py';text=legacy.read_text(encoding='utf-8')
report={
 'legacy_lines':len(text.splitlines()),
 'legacy_classes':len(re.findall(r'^class ',text,re.M)),
 'center_modules':len(list((ROOT/'github_command_center/centers').rglob('*.py'))),
 'service_modules':len(list((ROOT/'github_command_center/services').glob('*.py'))),
 'legacy_sync_heavy_calls':len(re.findall(r'git\(self\.repo,"(?:fetch|fsck|gc|maintenance|clone|bundle|submodule|push|pull)',text)),
 'migrated_async_centers':['AsyncFetchCenter','AsyncRemotePruneCenter','AsyncMaintenanceCenter'],
}
(ROOT/'architecture-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
