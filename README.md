# GitHub Command Center v3.61.0

Version 3.61 continues the stabilization track instead of returning to feature accumulation.

## Verified Update Center
- Load signed-release metadata JSON
- Enforce numeric major/minor/patch update policy
- Verify downloaded installer SHA-256
- Show notes/installer/signature URLs
- Never silently installs or launches an installer

## Release gating
A new release-gate workflow requires CI, Windows validation and the Windows UI-regression matrix before the release-ready job succeeds. Existing Windows package smoke tests remain part of packaging evidence.

## Authenticode
The optional v3.60 signing hooks remain supported. When certificate secrets are configured the package workflow signs and verifies the Windows executable before packaging continues.

## Architecture
v3.59 legacy retirement and architecture budgets remain enforced. New UI development stays outside `local_git_gui.py`.
