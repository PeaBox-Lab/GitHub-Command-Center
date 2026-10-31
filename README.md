# GitHub Command Center v3.24.0

Version 3.24 continues the major-version-3 decimal train with worktree repair, expanded tag management, and a safe pathspec exploration tool.

## New in v3.24

### Worktree Repair Center
- Inspect worktree porcelain state
- Run `git worktree repair`
- Prune dry-run with verbose output
- Confirmed stale-worktree metadata pruning

### Tag Manager Pro
- Annotated tags
- Signed tags
- Select an explicit target ref
- Inspect tags
- Verify signed tags
- Push individual tags
- Delete local tags
- Delete remote tags only after exact typed confirmation

### Pathspec Explorer
- Safely preview Git pathspecs against tracked files
- Preview changed files matching a pathspec
- Supports normal patterns and Git pathspec magic such as `:(glob)` and `:(exclude)`
- Read-only exploration before using a complex pathspec elsewhere

All v0.1-v3.23 capabilities remain available through Command Palette.
