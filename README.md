# GitHub Command Center v3.14.0

Version 3.14 continues decimal versioning within major version 3. This release adds stronger provenance, release comparison and guarded branch cleanup.

## Signature Audit Center
- Review the latest 10-1,000 commits
- Git signature-status codes translated into readable states
- Summary of good, bad, expired, unknown-trust and unsigned commits
- Inspect full signature output for a selected commit
- Export audit report

## Release Comparison Center
- Compare any two tags/refs
- Commit count and short diff statistics
- File-level status inventory
- Commit inventory
- Export review as Markdown

## Safe Branch Delete Wizard
- Checks current-branch state
- Detects branch use by worktrees
- Requires Git to report the branch as merged
- Checks local commits ahead of configured upstream
- Only normal `git branch -d`
- Force deletion is intentionally unavailable

All v0.1-v3.13 tools remain available through Command Palette.
