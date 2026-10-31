# GitHub Command Center v3.28.0

Version 3.28 continues decimal progression within major version 3 and adds guarded merge-commit reverts, repository acceleration maintenance, and configurable diff-algorithm analysis.

## New in v3.28

### Merge Commit Revert Center
- Browse merge commits and their parents
- Inspect each parent before choosing mainline
- Preview the merge-side change to be inverted
- Validate selected mainline parent
- Automatic `gccc-backup/pre-merge-revert-*` safety branch
- Continue or abort after conflicts

### Commit Graph & Pack Index Center
- Detect commit-graph and multi-pack-index files
- Write and verify commit graph with changed-path Bloom filters
- Write bitmap-enabled multi-pack-index
- Verify multi-pack-index
- Confirmed expiration of redundant packs
- Object database statistics

### Diff Algorithm Lab
- Myers
- Minimal
- Patience
- Histogram
- Optional word-diff output
- Compare working changes or two refs
- Optional path filter

All v0.1-v3.27 capabilities remain included through Command Palette.
