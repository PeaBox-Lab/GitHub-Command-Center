# GitHub Command Center v3.0.0

An extensible Python desktop platform for Git, GitHub and multi-repository engineering workflows. Version 3.0 is an extensive bundled release that adds a safer plugin model, portfolio batch operations, an operational dashboard and structured data export while retaining every prior center.

## New platform capabilities
### Plugin Manager
- Repository-local JSON command plugins under `.git/gccc-plugins`
- Create, inspect, enable/disable, run and delete plugins
- Commands execute as argument arrays without shell interpolation
- Confirmation before execution and captured stdout/stderr/exit code
- Opens the plugin folder for manual review

### Batch Operations Center
- Scan a workspace containing multiple Git repositories
- Multi-select repositories
- Sequential fetch/prune, status, Git integrity, Python compile or FF-only pull
- FF-only pull skips repositories with local changes
- Per-repository results remain visible in the grid
- No force operations

### Repository Operations Dashboard
- Current branch, upstream, ahead/behind state, working-tree count, last commit and recent tags
- Documentation-control status for README, CHANGELOG, LICENSE, SECURITY and CONTRIBUTING
- Contextual next-action recommendation
- Quick links to Smart Sync, Pre-Commit Review and Release Policy

### Repository Data Export
- JSON export for repository metadata, remotes, tags and up to 500 commits
- CSV export for commit hash, date, author, email and subject
- Built-in preview without external analytics

## Cumulative feature platform
Includes every v0.1-v2.2 capability: GitHub dashboard, comprehensive local Git workspace, visual graph/conflicts, advanced history operations, Releases, PRs, Actions, Security, Health, Worktrees, Compare/Recovery, portfolio management, diagnostics, Smart Sync, review/notes, cleanup/snapshots, patches/bisect, inspection/submodules, tasks/archive, Command Palette, Hooks, LFS, automation recipes, identity/signing, commit/changelog studios, remote migration, credential hygiene, release policy and metrics.

## Requirements
Python 3.10+ and Git. GitHub CLI is required for hosted GitHub workflows. Optional GPG, Git LFS, pip-audit and Bandit integrations remain supported.
