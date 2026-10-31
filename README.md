# GitHub Command Center v3.30.0

Version 3.30 continues decimal progression within major version 3 with patch-series comparison, refspec dry-run tooling, and Git-notes merge workflows.

## New in v3.30

### Range-Diff Center
- Compare two commit ranges using `git range-diff`
- Ideal for reviewing a patch series before/after rebase
- Shows changed, reordered, added, removed, and equivalent patches
- Export comparison report

### Refspec Lab
- Inspect configured remote fetch/push refspecs
- Compose explicit source:destination mappings
- Dry-run fetch with a candidate refspec
- Dry-run push with a candidate refspec
- Does not silently persist refspec configuration

### Git Notes Merge Center
- Browse notes refs
- Merge one notes ref into another
- Strategies: manual, ours, theirs, union, cat_sort_uniq
- Commit or abort a notes merge
- Notes operations do not change commit IDs

All v0.1-v3.29 capabilities remain included through Command Palette.
