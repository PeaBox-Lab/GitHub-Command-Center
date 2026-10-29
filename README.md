# GitHub Command Center v3.1.0

Extensible Python desktop platform for Git, GitHub and repository portfolios. Version 3.1 implements major roadmap foundations: cancellable background jobs, persistent preferences, SQLite portfolio history and built-in self-tests.

## New bundled platform capabilities
### Background Jobs Center
- Queue long-running local commands without freezing the center
- Direct argument-array execution without a shell
- Live status, output log and exit code
- Cancel active local processes
- Clear completed jobs

### Preferences & Appearance
- Persist Tk theme, editor font-size default, history-row limit, destructive-confirmation preference and default base branch
- Stored outside repositories in `~/.gccc-preferences.json`
- Theme applies immediately

### Portfolio History
- SQLite-backed snapshots under `~/.gccc-portfolio.sqlite3`
- Capture branch, clean/changed status and upstream ahead/behind state across a workspace
- Browse the latest 1,000 snapshot rows
- Export complete snapshot history to CSV

### Self-Test & Readiness
- Git availability and repository validation
- HEAD, status and log parser smoke tests
- Configuration-path check
- Python source compilation test
- Overall PASS/FAIL and exportable report

## Cumulative platform
Every feature from v0.1 through v3.0 remains available through the searchable Command Palette, including plugins, batch operations, repository dashboard, exports, local Git, visual graph/conflicts, Releases, PRs, Actions, Security, Health, Worktrees, Recovery, Hooks, LFS, signing, release policy and metrics.

## Requirements
Python 3.10+ and Git. GitHub CLI is required for GitHub-hosted workflows. SQLite support is included with standard Python.
