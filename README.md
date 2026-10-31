# GitHub Command Center v3.23.0

Version 3.23 continues decimal progression within major version 3 and adds guided modern switch/restore operations, live rebase-state inspection, and Git describe/version utilities.

## New in v3.23

### Switch & Restore Center
- Switch existing branches
- Create + switch branches
- Restore one path from HEAD or another ref
- Restore working tree only or staged + working state
- Diff preview and confirmation before destructive restore

### Rebase State Inspector
- Detect active `rebase-merge` or `rebase-apply` state
- Show head-name, onto, original HEAD, completed actions, remaining todo, stopped commit and message
- Display unresolved files
- Continue, skip or abort
- Edit/save interactive rebase todo when available

### Git Describe & Version Center
- Nearest tag/commit description
- Long form with distance, abbreviated hash and dirty state
- Exact-tag detection
- Copy generated version string for release/build workflows

All v0.1-v3.22 tools remain included through Command Palette.
