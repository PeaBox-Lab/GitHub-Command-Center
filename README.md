# GitHub Command Center v3.59.0

Version 3.59 is the legacy-retirement, async-completion and architecture-enforcement release.

## Retired duplicate legacy implementations

Twelve migrated class bodies were removed from `local_git_gui.py` and replaced with thin compatibility aliases to extracted centers:

- Release Center
- Pull Requests
- GitHub Actions
- Security
- Commit Inspector
- Reflog Recovery
- Maintenance
- Preflight
- Local Branch Dashboard
- Remote Prune Audit
- Fetch Preview
- Branch Protection Advisor

Existing callers remain compatible, but only the extracted implementation is maintained.

## Synchronous GitHub cleanup

Direct synchronous `gh` subprocess wrappers inside retired centers were removed. The remaining authentication path now opens the asynchronous GitHub center. GitHub queries and mutations use JobService/JobPanel with argument arrays, streamed output, cancellation and exit status.

## Architecture enforcement

`scripts/architecture_gate.py` fails CI when the legacy module, synchronous heavy operations, direct synchronous GitHub calls or `shell=True` regress beyond approved limits. The limits only move downward in future releases.

## Current direction

v3.60 is the stabilization milestone: submodule/LFS/clone async migration, updater verification, Windows release gating and signing hooks.
