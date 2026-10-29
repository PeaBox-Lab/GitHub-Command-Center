# GitHub Command Center v0.5.0

Python desktop replacement for everyday GitHub web and TortoiseGit workflows.

## New Release Center
- Release-readiness report for clean tree, branch, origin, upstream, ahead/behind state, README, CHANGELOG, LICENSE, and GitHub CLI
- Generate Markdown release notes from commits since the latest tag
- Create and push annotated version tags
- Publish GitHub releases using authenticated GitHub CLI
- Draft and pre-release options
- Upload multiple release assets
- Create a full repository Git bundle containing branches and tags
- Export a clean ZIP of current HEAD without `.git`
- Built-in recovery commands for Git bundles

## Existing capabilities
- GitHub statistics, repositories, activity, insights, issue and repository creation
- Local clone/init, status, stage/unstage, commit, fetch, FF-only pull, push, diff and history
- Visual branch/merge commit graph
- Three-pane conflict resolver
- Branch, merge, stash, tag, remote and cleanup tools
- Cherry-pick, safe rebase, revert, reset safety backups, and `.gitignore` editor

## Windows requirements
- Python 3.10+
- Git on PATH
- GitHub CLI `gh` and `gh auth login` only for publishing GitHub releases

Extract and double-click `run_windows.bat`.
