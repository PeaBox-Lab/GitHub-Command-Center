# GitHub Command Center v3.40.0

Version 3.40 continues decimal progression within major version 3 with multi-branch topology comparison, ref-relative object naming, and local object-database growth tracking.

## New in v3.40

### Show-Branch Explorer
- Compare multiple branch/ref tips with `git show-branch`
- Use `--all` or explicit space-separated refs
- Configure additional history depth
- Export topology report

### Name-Rev Explorer
- Convert object IDs/revisions into human-readable ref-relative names
- Optional tag-only naming
- `--always` fallback
- Name all reachable revisions

### Object Growth Tracker
- Capture `git count-objects -vH` snapshots
- Store local history under `.git/gccc-object-trends.json`
- Compare loose objects, packed objects, pack size, and garbage between snapshots
- Export CSV
- Direct access to Maintenance Center

All v0.1-v3.39 capabilities remain included through Command Palette.
