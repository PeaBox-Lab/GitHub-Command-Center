# GitHub Command Center v3.33.0

Version 3.33 continues decimal progression within major version 3 with explicit lost-object preservation, shallow-clone history controls, and porcelain-v2 status analysis.

## New in v3.33

### Lost & Found Center
- Run `git fsck --lost-found`
- Inventory `.git/lost-found/commit` and `.git/lost-found/other`
- Inspect recovered commit patches or raw objects
- Preserve a recovered commit by creating a local recovery branch
- Export inventory
- No object deletion

### Shallow Repository Center
- Detect shallow clones
- Show reachable commit count and boundary view
- Deepen history by a selected number of commits
- Fetch tags
- Fetch complete history with confirmation

### Status Porcelain Explorer
- Parse `git status --porcelain=v2 --branch`
- Show record type, XY state, submodule state, path, and raw details
- Branch headers and raw output
- Copy/export for automation diagnostics

All v0.1-v3.32 tools remain included through Command Palette.
