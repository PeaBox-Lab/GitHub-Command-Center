# GitHub Command Center v3.13.0

Version 3.13 continues decimal versioning within major version 3 and strengthens multi-commit integration and release-artifact integrity.

## Cherry-Pick Queue Center
- Browse up to 250 commits
- Build an ordered multi-commit queue
- Reorder and remove queue items
- Clean-tree gate
- Automatic timestamped pre-cherry-pick backup branch
- Apply the queue in order
- Continue or abort after conflicts

## Release Asset Integrity
- Select multiple release artifacts
- Generate SHA-256 checksums
- Save `SHA256SUMS.txt`
- Verify an existing checksum manifest against files in its folder
- PASS, FAIL, MISSING and invalid-line results

## Local Release Archive
- Clean-tree gate
- Create a versioned release folder
- Clean source ZIP from HEAD
- Full repository Git bundle
- Copy release notes when present
- SHA-256 manifest
- JSON metadata with repository, version, timestamp, branch and HEAD

All earlier v0.1-v3.12 capabilities remain included through Command Palette.
