# GitHub Command Center v3.31.0

Version 3.31 continues decimal progression within major version 3 with merge-strategy experimentation, Git configuration include-chain visibility, and packed-object inventory analysis.

## New in v3.31

### Merge Strategy Lab
- Preview a target ref using merge-base and merge-tree
- Strategies: ort, recursive, resolve, octopus, ours, subtree
- Strategy options such as ours, theirs, patience, histogram, ignore-space-change, and renormalize
- Actual merge starts with `--no-commit --no-ff`
- Explicit abort control and clean-tree gate

### Config Include Inspector
- Inspect `include.path` and conditional `includeIf.*.path` rules
- Show scope and origin
- Display the effective configuration with includes resolved
- Export the report

### Pack Inventory Center
- Pack-index inventory
- Git object database statistics
- Read-only `verify-pack` analysis
- Largest packed blobs with best-effort path mapping
- Exportable report and handoff to Maintenance Center

All v0.1-v3.30 tools remain included through Command Palette.
