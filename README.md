# GitHub Command Center v3.37.0

Version 3.37 continues decimal progression within major version 3 with commit-message quality auditing, revision manifests, and local branch-purpose documentation.

## New in v3.37

### Commit Message Audit
- Audit any commit range
- Conventional Commit coverage
- Minimum subject-length checks
- Generic subject detection
- Merge commit counts
- Per-commit assessment and exportable summary

### Revision Manifest Center
- Generate a manifest of mode, object type, blob/tree ID, and path for any revision
- Record the resolved commit ID
- Export manifest
- Verify a manifest against another selected revision
- Report added, missing, and changed blobs without checkout

### Branch Description Center
- Inventory local branches and descriptions
- Edit `branch.<name>.description`
- Clear descriptions
- Store branch purpose/notes as local Git config metadata
- Does not alter commits or push descriptions remotely

All v0.1-v3.36 tools remain included through Command Palette.
