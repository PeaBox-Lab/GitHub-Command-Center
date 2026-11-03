from __future__ import annotations
import json,re,tomllib,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];VERSION='3.79.0'
py=tomllib.loads((ROOT/'pyproject.toml').read_text());init=(ROOT/'github_command_center/__init__.py').read_text();fail=[]
checks={
'pyproject_version':py['project']['version']==VERSION,
'package_version':f'__version__ = "{VERSION}"' in init,
'console_entry_point':py['project']['scripts'].get('github-command-center')=='github_command_center.app:main',
'coverage_gate':py['tool']['coverage']['report']['fail_under']>=70,
'architecture_gate':(ROOT/'scripts/architecture_gate.py').exists(),
'security_gate':(ROOT/'scripts/security_gate.py').exists(),
'packaging_gate':(ROOT/'scripts/packaging_gate.py').exists(),
'ci':(ROOT/'.github/workflows/ci.yml').exists(),
'codeql':(ROOT/'.github/workflows/codeql.yml').exists(),
'dependency_review':(ROOT/'.github/workflows/dependency-review.yml').exists(),
'release_security':(ROOT/'.github/workflows/release-security.yml').exists(),
}
for k,v in checks.items():
 if not v:fail.append(k)
report={'version':VERSION,'checks':checks,'passed':not fail,'failures':fail}
(ROOT/'release-readiness.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(bool(fail))
