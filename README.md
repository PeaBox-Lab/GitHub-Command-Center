# GitHub Command Center v3.19.0

Version 3.19 continues decimal progression in major version 3 and adds deeper source attribution, safer remote-ref cleanup, and read-only Git object inspection.

## New in v3.19

### Blame Explorer
- Line-by-line blame table
- Commit, author, date and content
- Inspect the commit responsible for a selected line
- Supports a selected revision and tracked path
- Handoff to existing Commit Inspector

### Remote Prune Audit
- Inventory configured remotes
- Dry-run stale-ref pruning for each remote
- Explicit prune of a selected remote
- Fetch all with prune
- Does not delete local branches

### Git Object Inspector
- Resolve refs/object IDs
- Object type and size
- Pretty-print object content
- Recursive tree listing
- Verify an object/ref
- Read-only plumbing workflow

All v0.1-v3.18 functionality remains included through Command Palette.
