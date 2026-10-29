# GitHub Command Center v2.0.0

An extensible Python desktop command center for GitHub and local Git, designed to replace routine TortoiseGit menus and frequent GitHub.com navigation.

## Why 2.0
The application now contains a broad toolset. Version 2.0 introduces a searchable Command Palette so features remain discoverable without expanding the main toolbar indefinitely. New feature centers are modular top-level classes, making future centers easy to register in the palette.

## Major bundled updates
### Searchable Command Palette
- Launch every advanced center by name or keyword
- Includes visual history, conflicts, releases, PRs, Actions, security, health, worktrees, compare, recovery, diagnostics, sync, review, patches, bisect, submodules, tasks, archive and new v2.0 tools
- Reduces toolbar clutter and provides an extensible registration pattern

### Git Hooks Manager
- Edit repository-local pre-commit, commit-msg and pre-push hooks
- Safe built-in templates for whitespace, Python syntax and commit-message length
- Save and enable executable hooks, disable hooks, and test hooks

### Git LFS Center
- Inspect Git LFS environment, tracked patterns and LFS files
- Track/untrack patterns such as `*.zip`
- Pull LFS objects and safely prune old local LFS data
- Explicitly notes that untracking does not rewrite existing history

### Automation Recipes
- Repository-local JSON recipes under `.git/gccc-recipes.json`
- Built-in Python syntax, Git integrity and whitespace recipes
- Add/delete/reset recipes and run commands with captured output and exit code
- Local-only storage keeps personal automation outside repository history

## Cumulative capabilities
Includes every feature from v0.1 through v1.6: GitHub dashboard, local Git workspace, visual graph, conflict resolution, branches, tags, stash, remotes, rebase, cherry-pick, reset safety, releases, PRs, Actions, security, repository health, worktrees, compare, recovery, multi-repository management, diagnostics, smart sync, search, pre-commit review, notes, cleanup, snapshots, patches, bisect, commit inspection, submodules, tasks and archive/handover.

## Windows
Extract and run `run_windows.bat`. Requires Python 3.10+ and Git. GitHub CLI is required for Releases, PRs, Actions and GitHub security APIs. Git LFS is optional for LFS features.
