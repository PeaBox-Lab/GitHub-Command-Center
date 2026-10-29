# GitHub Command Center v3.5.0

Version 3.5 bundles four essential Git capabilities for large repositories, maintenance, non-rewriting metadata and external comparison tools.

## Sparse Checkout Center
- Cone-mode initialization
- Select top-level folders to materialize
- Add another sparse path
- Restore the full working tree
- Clean-working-tree safety gate

## Repository Maintenance Center
- Object database size/count analysis
- `git maintenance run --auto`
- Normal `git gc`
- Full `git fsck`
- Commit-graph generation with changed paths
- Optional Git scheduled-maintenance registration
- No aggressive GC or immediate reflog expiration

## Git Notes Center
- Browse 200 recent commits
- Read, add, replace and remove notes
- Custom notes refs
- Explicit push of a notes ref to origin
- Commit hashes remain unchanged

## Diff & Merge Tool Center
- Repository-level setup for VS Code, WinMerge, Beyond Compare or KDiff3
- Launch difftool for all changes or one path
- Launch mergetool for unresolved conflicts
- Displays current diff/merge tool configuration

All earlier features remain available through Command Palette. Decimal versioning remains within major version 3.
