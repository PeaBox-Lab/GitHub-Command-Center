# GitHub Command Center v3.15.0

Version 3.15 continues the decimal major-version-3 train with safer synchronization decisions, detached-HEAD recovery and auditable repository-state exports.

## Pull Strategy Advisor
- Fetch/prune and inspect ahead/behind state
- Explain whether fast-forward, push, merge or rebase is appropriate
- Fast-forward-only pull
- Protected rebase with timestamped backup branch
- Explicit upstream merge
- Never selects a history-changing strategy silently

## Detached HEAD Recovery
- Detect detached HEAD
- Show exact HEAD and commit metadata
- Create and switch to a recovery branch at the current commit
- Switch back to the origin default branch with confirmation

## Repository State Export
- JSON snapshot for automation/audit
- Markdown handover snapshot
- Branch, HEAD, upstream, changes, remotes, tags and recent commits

All v0.1-v3.14 features remain available through Command Palette.
