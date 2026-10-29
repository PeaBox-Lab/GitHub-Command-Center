# GitHub Command Center v0.8.0

Python desktop command center for GitHub and local Git workflows.

## New in v0.8.0: Repository Health Center
- 100-point repository-health score
- Checks README, LICENSE, CHANGELOG, SECURITY, CONTRIBUTING, issue/PR templates, CODEOWNERS, `.gitignore`, `.gitattributes`, CI workflows, tests, tags, and working-tree cleanliness
- Repository governance-file inventory
- Actionable list of missing quality controls
- One-click generation of SECURITY.md, CONTRIBUTING.md, bug/feature issue templates, pull-request template, CODEOWNERS and `.gitattributes`
- Existing files require confirmation before replacement

## New in v0.8.0: Git Worktree Center
- View all linked worktrees, branch and HEAD
- Create a worktree for an existing branch
- Create a new branch and worktree together
- Safely remove a secondary worktree
- Prune obsolete worktree metadata

## Cumulative capabilities
- GitHub dashboard, repositories, issues and account insights
- Local Git workspace with status, staging, commit, fetch, FF-only pull, push and diff
- Visual commit graph and three-pane merge conflict resolution
- Branch, merge, stash, tag, remote, cherry-pick, rebase, revert and guarded reset workflows
- Release Center, Pull Request Center and GitHub Actions Center
- Security Center with Dependabot/code/secret scanning views, local audits and checksums
- Git bundle and ZIP backup/export

## Requirements
Python 3.10+, Git. Authenticated GitHub CLI is required for GitHub Releases, PRs, Actions and GitHub security APIs.
