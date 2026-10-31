# GitHub Command Center v3.26.0

Version 3.26 continues decimal progression within major version 3 and adds advanced ref/object interpretation and commit-reachability analysis tools.

## New in v3.26

### Git Replace Center
- List local `refs/replace/*`
- Create a local replace ref between two verified objects
- Inspect original and replacement objects
- Remove replace refs with confirmation
- Does not rewrite underlying objects

### Merge Base Explorer
- Primary and all merge bases between refs
- Ahead-side commit counts
- `--is-ancestor` analysis
- Fork-point analysis
- Independent-tip calculation

### Commit Reachability Explorer
- Inspect any commit/ref
- Local + remote branches containing a commit
- Tags containing a commit
- Branches not merged into a selected ref
- Useful before cleanup, backport, release and branch-deletion decisions

All v0.1-v3.25 features remain available through Command Palette.
