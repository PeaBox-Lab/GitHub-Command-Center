# GitHub Command Center v3.38.0

Version 3.38 continues decimal progression within major version 3 with path-selective stashing, linked-worktree relocation, and effective Git-configuration snapshot comparison.

## New in v3.38

### Selective Stash Center
- Inventory changed paths
- Multi-select exact paths to stash
- Named stash message
- Optional `--keep-index`
- Optional `--include-untracked`
- Uses explicit pathspec after `--`

### Worktree Move Center
- Inventory linked worktrees
- Choose destination folder
- Clean-worktree gate on the selected linked worktree
- Move with `git worktree move`
- Prevent moving the primary worktree through this workflow
- Repair all worktree metadata

### Git Config Snapshot Compare
- Capture effective configuration baseline
- Includes scope, origin, and resolved include files
- Compare current effective config using unified diff
- Export comparison report
- Direct access to Git Configuration Center

All v0.1-v3.37 capabilities remain included through Command Palette.
