from __future__ import annotations
import argparse, ast, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'github_command_center'
WORKFLOWS=ROOT/'.github/workflows'

def error_metrics():
    bare=broad=0
    for path in PACKAGE.rglob('*.py'):
        tree=ast.parse(path.read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node,ast.ExceptHandler):
                bare += node.type is None
                broad += isinstance(node.type,ast.Name) and node.type.id=='Exception'
    return bare,broad

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='security-gate.json');args=ap.parse_args()
    bare,broad=error_metrics()
    workflow_text='\n'.join(p.read_text(encoding='utf-8') for p in WORKFLOWS.glob('*.yml'))
    metrics={
      'bare_exception_handlers':bare,
      'broad_exception_handlers':broad,
      'shell_true':sum(len(re.findall(r'shell\s*=\s*True',p.read_text(encoding='utf-8'))) for p in PACKAGE.rglob('*.py')),
      'ci_workflows':len(list(WORKFLOWS.glob('*.yml'))),
      'codeql': 'github/codeql-action/' in workflow_text,
      'dependency_review':'actions/dependency-review-action@' in workflow_text,
      'artifact_attestation':'actions/attest@' in workflow_text,
      'pip_audit':'pip-audit' in workflow_text,
      'bandit':'bandit ' in workflow_text,
      'ruff':'ruff check' in workflow_text,
      'no_branch_action_refs': not bool(re.search(r'uses:\s*[^\s]+@(main|master|develop|dev)\b',workflow_text)),
    }
    required=['codeql','dependency_review','artifact_attestation','pip_audit','bandit','ruff','no_branch_action_refs']
    failures=[]
    if bare: failures.append(f'bare exception handlers: {bare}')
    if broad: failures.append(f'broad exception handlers: {broad}')
    if metrics['shell_true']: failures.append(f'shell=True uses: {metrics["shell_true"]}')
    for key in required:
        if not metrics[key]: failures.append(f'missing {key}')
    report={'version':'3.77.0','metrics':metrics,'passed':not failures,'failures':failures}
    (ROOT/args.output).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));return 1 if failures else 0
if __name__=='__main__': raise SystemExit(main())
