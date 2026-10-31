# GitHub Command Center v3.54.0

Version 3.54 prioritizes architecture extraction and async migration.

## Extracted sync domain

New independent center package:

```text
centers/sync/
├── base.py
├── fetch_center.py
├── remote_prune_center.py
└── maintenance_center.py
```

The Command Palette now routes Fetch Preview, Remote Prune Audit, and Repository Maintenance to these extracted modules rather than the legacy compatibility implementations.

## Async migrations

### Fetch
- dry-run preview remains immediate
- actual fetch runs through JobService
- streamed output, exit code, cancellation

### Remote prune
- dry-run preview
- selected remote prune in background
- fetch-all/prune in background

### Maintenance
- auto/scheduled maintenance
- full fsck
- normal gc
- commit graph write/verify
- multi-pack-index write
- all expensive actions use JobService

## Architecture audit

`scripts/architecture_audit.py` records legacy LOC/classes, center/service module counts, remaining synchronous heavy calls, and migrated async centers as JSON evidence.
