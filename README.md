# GitHub Command Center v3.39.0

Version 3.39 continues decimal progression within major version 3 with fixup/squash commit authoring, tracked-file index-flag management, and advanced revision-walk exploration.

## New in v3.39

### Fixup & Squash Commit Center
- Browse recent commits
- Create `--fixup=<commit>` commits from staged changes
- Create `--squash=<commit>` commits
- Amend HEAD using staged changes and `--no-edit`
- Automatic `gccc-backup/pre-amend-*` branch before amend
- Direct handoff to Interactive Rebase for autosquash

### Tracked File Flags Center
- Inspect `git ls-files -v` flags
- Set/clear assume-unchanged
- Set/clear skip-worktree
- Multi-select paths
- Explicit confirmation
- Explains that these are local index hints, not ignore rules

### Revision Walk Lab
- Custom revision specification
- Topological, date, or author-date order
- First-parent walks
- Ancestry-path filtering
- Boundary commits
- Graph/decorated one-line output

All v0.1-v3.38 capabilities remain included through Command Palette.
