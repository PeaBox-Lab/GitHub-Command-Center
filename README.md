# GitHub Command Center v3.21.0

Version 3.21 continues decimal progression within major version 3 and adds three deeper Git tools for object recovery, contributor identity normalization, and equivalent-patch detection.

## New in v3.21

### Dangling Object Recovery
- Scan unreachable/dangling objects with `git fsck --no-reflogs --unreachable`
- Identify unreachable commits, trees, blobs, and tags
- Inspect unreachable commit patches or raw object content
- Preserve an unreachable commit by creating a local recovery branch
- Export the complete fsck evidence report
- No object deletion

### Contributor Mailmap Center
- Inventory raw contributor names and emails
- Edit repository `.mailmap`
- Preview canonical contributor shortlog
- Normalize reporting without rewriting commits

### Patch Identity Comparator
- Stable `git patch-id` comparison for two commits
- Detect equivalent changes independent of author/date/message
- `git cherry -v` range comparison
- Useful for duplicate cherry-picks and rebased-equivalent commits

All prior v0.1-v3.20 capabilities remain included through Command Palette.
