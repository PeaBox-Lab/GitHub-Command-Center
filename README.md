# GitHub Command Center v3.56.0

Version 3.56 continues architecture extraction and asynchronous network/backup migration.

## Extracted centers

```text
centers/sync/push_pull_center.py
centers/backup/bundle_center.py
```

### Async Push & Pull Center
- remote/branch selection
- ff-only, rebase, or merge pull strategies
- normal, set-upstream, or force-with-lease push
- clean-tree and detached-HEAD safeguards
- background JobService execution with live output and cancellation

### Async Git Bundle Center
- create complete `--all` bundles in the background
- verify bundles in the background
- list bundle heads through GitService
- explicit destination selection and confirmation

## Migration status

Eight primary centers now route outside the legacy GUI implementation. The next architecture phase should target submodules/LFS and GitHub network/release publishing operations.
