# GitHub Command Center v3.41.0

Version 3.41 continues decimal progression within major version 3 with exact ref verification, batch ignore-rule provenance testing, and dry-run fetch analysis.

## New in v3.41

### Ref Verification Center
- Resolve and verify an exact ref/object expression
- Display object type
- Show matching refs
- Peel annotated tags/refs to objects and commits
- Inspect symbolic refs
- Inspect recent reflog entries
- Read-only safety utility

### Ignore Rule Batch Tester
- Test many repository-relative paths at once
- Verbose ignore provenance via `git check-ignore -v --no-index`
- Show the source ignore file, rule line, and pattern
- Load current untracked paths automatically
- Direct access to Ignore & Attributes Studio

### Fetch Preview Center
- Dry-run a fetch before changing remote-tracking refs
- Select remote
- Optional custom refspec
- Optional prune and tag fetching
- Execute the exact reviewed fetch after confirmation

All v0.1-v3.40 capabilities remain included through Command Palette.
