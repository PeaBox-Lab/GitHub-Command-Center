# GitHub Command Center v0.6.0

A Python desktop command center replacing routine GitHub web and TortoiseGit workflows.

## New in v0.6.0: Pull Request Center
- View up to 100 open, closed, merged, and draft pull requests
- Inspect PR details and comments
- Create a pull request from the current branch
- Checkout a PR locally
- Merge using merge commit, squash, or rebase
- Delete the PR branch after merge
- Open a selected PR in GitHub only when needed

## New in v0.6.0: GitHub Actions Center
- View the latest 100 workflow runs
- Workflow, branch, event, status, conclusion, and creation time
- View workflow logs
- Re-run a selected workflow run
- Cancel a running workflow
- Manually dispatch a workflow

## Previous capabilities retained
- GitHub dashboard and repository/issue management
- Complete local Git workspace with staging, commit, sync, branches, tags, stash and remotes
- Visual commit graph and merge conflict resolver
- Cherry-pick, safe rebase, revert, reset safeguards and `.gitignore` editor
- Release Center with readiness checks, release notes, tags, assets, GitHub releases, Git bundles and ZIP exports

## Requirements
Python 3.10+, Git. GitHub CLI `gh` authenticated with `gh auth login` is required for Releases, Pull Requests and Actions.
