# GitHub Command Center v3.3.0

Python desktop command center for Git and GitHub. Version 3.3 follows decimal progression and delivers two critical Git workflows: partial hunk staging and safe reflog recovery.

## Partial Staging Center
- Lists changed files and parses unstaged text patches into individual hunks
- Preview each selected hunk
- Stage only one hunk using `git apply --cached`
- Browse staged hunks and unstage only one hunk using reverse cached patch application
- Stage or unstage the complete file when appropriate
- Handles renamed paths in status output
- Does not silently stage unrelated hunks

Partial hunk operations apply Git-generated patches. Binary files, untracked files without a normal diff, and unusually complex combined patches should be staged as complete files.

## Reflog Recovery Center
- Browse up to 500 reflog entries across all refs
- Entry selector, full/short hash, timestamp, action and message
- Inspect the selected commit before recovery
- Safest recovery action creates a new branch at the selected commit
- Optional detached checkout with warning
- Reflog expiry is dry-run preview only
- No hard reset and no reflog deletion

## UI integration
- Partial staging is directly available under Work
- Reflog Recovery is directly available under Tools
- Both are registered in the searchable Command Palette

All v0.1-v3.2 functionality remains included.
