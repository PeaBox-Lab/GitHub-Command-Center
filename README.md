# GitHub Command Center v3.48.0

Version 3.48 is the reliability milestone begun after the v3.41 audit.

## Reliability coverage

New real-Git integration tests cover:

- safety-branch preservation
- reflog recovery after hard reset
- branch-based commit recovery
- clean rebase
- conflict rebase abort and state restoration
- merge-conflict index stages 1/2/3
- merge abort
- resolving/staging ours
- annotated release tags
- source ZIP archive generation
- Git bundle creation/verification
- recovery-policy decisions
- repository performance probes

The suite now combines unit, parser, policy, service, packaging, and real temporary-repository tests.

## ReliabilityService

`services/reliability.py` adds repeatable timings for:

- repository status
- 100-commit log
- refs
- object counts

Results can be persisted as JSON for future trend comparison.

## Recovery policy

`services/recovery_policy.py` centralizes a non-destructive recovery preference:

1. reflog branch
2. direct branch from known commit
3. fsck/unreachable branch
4. verified bundle/backup

The policy never chooses reset as the first preservation action.

## CI evidence

CI now runs `scripts/reliability_report.py` and uploads `reliability-report.json` for each OS/Python matrix entry, alongside the existing compile, test, Ruff, Bandit, and pip-audit gates.
