# GitHub Command Center v3.9.0

Version 3.9 continues the major-3 decimal release train with safer rewritten-history publishing, deeper history search and stronger offline bundle validation.

## Force-with-Lease Safety Center
- Current branch/upstream and ahead/behind review
- Explicit fetch of origin before publishing rewritten history
- Shows local and observed upstream commit IDs
- Only `--force-with-lease`, never plain `--force`
- Exact typed branch-name confirmation plus final confirmation
- Detached HEAD blocked

## Advanced History Search
- Commit-message search across all refs
- Pickaxe `-S` search for additions/removals of specific text
- Diff-regex `-G` search
- Optional tracked-path filter
- Rename-aware file history

## Git Bundle Inspector
- Select an existing `.bundle`
- Verify bundle integrity/prerequisites
- List contained refs/heads
- Clone a verified bundle into a new local repository folder

All v0.1-v3.8 tools remain included and available through Command Palette.
