# GitHub Command Center v3.55.0

Version 3.55 is architecture phase 2.

## Extracted domains

```text
centers/branches/dashboard.py
centers/recovery/dashboard.py
centers/release/evidence.py
```

The Command Palette now routes Branch Dashboard, Reflog Recovery, and Release Evidence to extracted domain modules using GitService and shared UI components.

## Async progress
- Release Evidence integrity (`git fsck --full`) now uses JobService/JobPanel.
- Branch and recovery inventory remain lightweight GitService reads.
- Recovery continues to preserve commits by creating a branch rather than resetting existing history.

## Current migration set

Six primary centers now route outside the legacy GUI: async fetch, remote prune, maintenance, branch dashboard, recovery dashboard, and release evidence.
