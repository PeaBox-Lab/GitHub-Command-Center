# GitHub Command Center v0.9.0

Python desktop command center for GitHub and local Git workflows.

## New: Compare & Review Center
- Compare any local branch, remote-tracking branch, tag, or commit ref
- Ahead/behind commit counts
- Changed-file count, additions and deletions
- Name/status inventory
- Commit list unique to the compare ref
- Unified diff viewer
- Export a complete review report to text

This provides a visual pre-merge and pre-release review step without needing GitHub's compare page.

## New: Backup & Recovery Center
- Create timestamped `gccc-backup/*` checkpoint branches before risky work
- Inventory existing safety branches and stashes
- Create a full Git bundle with all refs
- Verify an existing bundle
- Restore a bundle into a new repository folder directly from the GUI

## Cumulative capabilities
- GitHub dashboard, repositories, issues and account insights
- Full local Git workspace and visual commit graph
- Three-pane merge conflict resolution
- Advanced branch, cherry-pick, rebase, revert and reset workflows
- Release, Pull Request and GitHub Actions centers
- Security & Dependency Center
- Repository Health Center and governance-template generators
- Git Worktree Center
- ZIP and Git bundle export

## Requirements
Python 3.10+, Git. Authenticated GitHub CLI is required for GitHub Releases, PRs, Actions and GitHub security APIs.
