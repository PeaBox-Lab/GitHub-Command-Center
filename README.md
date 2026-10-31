# GitHub Command Center v3.34.0

Version 3.34 continues decimal progression within major version 3 with sparse-index controls, scheduled-maintenance administration, and repository-format compatibility inspection.

## New in v3.34

### Sparse Index Center
- Inspect sparse-checkout state and configured paths
- Inspect `index.sparse`
- Enable sparse index using `sparse-checkout reapply --sparse-index`
- Disable sparse index using `--no-sparse-index`
- Clean-working-tree safety gate
- Open existing Sparse Checkout Center

### Maintenance Schedule Center
- Inspect globally registered maintenance repositories
- Register/unregister the current repository
- Set incremental or geometric maintenance strategy
- Run scheduled maintenance tasks immediately
- Show repository object status

### Repository Format Inspector
- Git version
- Repository format version
- Object format such as SHA-1/SHA-256
- Ref storage format when supported by installed Git
- Bare/shallow state
- Common and worktree Git directories
- Repository extension configuration
- Read-only exportable compatibility report

All v0.1-v3.33 tools remain included through Command Palette.
