# GitHub Command Center v3.4.0

Version 3.4 adds three major history and reference workflows while retaining all v0.1-v3.3 capabilities.

## Interactive Rebase Editor
- Load a first-parent commit plan after a chosen base ref
- Reorder commits with Move up/down
- Actions: pick, reword, edit, squash, fixup and drop
- Full commit/plan preview
- Automatic timestamped `gccc-backup/pre-rebase-*` safety branch
- Clean-working-tree gate
- Continue, skip and abort controls
- Conflict-aware paused-state messaging

## Unified Ref Browser
- One searchable view of local branches, remote branches, tags, stash, notes and other refs
- Commit hash, date and subject
- Inspect referenced commit
- Switch local branches or detached-checkout other refs
- Create a branch from any selected ref
- Safe deletion limited to normal local branch deletion and local tags
- Copy full ref name

## Repository History Browser
- Browse the complete file tree at HEAD, a branch, tag or commit
- Select from 150 recent commits
- Lazy-expand historical directories
- View text-file contents without checkout
- Export a historical file byte-for-byte
- Open Commit Inspector for deeper patch/blame work

The features are available in the sidebar and Command Palette. Decimal versioning remains within major version 3.
