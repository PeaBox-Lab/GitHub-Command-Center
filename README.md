# GitHub Command Center v1.0.0

Production-oriented Python desktop command center for GitHub and local Git workflows, designed to replace routine TortoiseGit menus and frequent visits to GitHub.com.

## v1.0 highlights
### Multi-Repository Manager
- Point the application at a workspace containing multiple Git repositories
- View current branch, clean/changed state, origin URL, and upstream ahead/behind counts
- Multi-select repositories and fetch/prune remotes
- Open a selected repository directly in the Local Git workspace

### Diagnostics & Configuration
- Python and operating-system details
- Git availability/version
- GitHub CLI availability/version
- Optional pip-audit and Bandit availability
- Git identity and key configuration values
- Repository `git fsck` integrity check
- Copyable diagnostic report for troubleshooting

## Complete capability set
- GitHub account dashboard, repository statistics, issues and repository creation
- Local clone/init, status, staging, commits, fetch, pull and push
- Visual commit topology graph
- Three-pane conflict-resolution editor
- Branches, merges, tags, remotes, stash, cherry-pick, rebase, revert and guarded reset
- `.gitignore` editor and safety backup branches
- Release Center with readiness checks, notes, tags, assets, releases, bundles and archive ZIPs
- Pull Request Center and GitHub Actions Center
- Security Center for Dependabot, code scanning, secret scanning, local audit and checksums
- Repository Health Center and governance-file generation
- Worktree management
- Branch/tag/ref comparison with exportable reports
- Backup and bundle recovery workflows
- Multi-repository portfolio management
- Diagnostics and environment reporting

## Windows quick start
1. Extract the ZIP.
2. Double-click `run_windows.bat`.
3. Connect GitHub with a fine-grained token for account APIs.
4. Use authenticated GitHub CLI (`gh auth login`) for Releases, PRs, Actions and security APIs.

Requires Python 3.10+ and Git on PATH.
