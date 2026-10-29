# GitHub Command Center v1.1.0

Python desktop command center for GitHub and local Git workflows.

## New in v1.1: Smart Sync Center
- Shows current branch, upstream, working-tree state, ahead count and behind count
- Fetches all remotes with pruning
- Recommends the safest next synchronization action
- Fast-forward-only pull when the remote is ahead
- Detects divergence and refuses to silently merge/rebase
- Does not auto-push local commits without explicit confirmation
- One-click timestamped pre-sync safety checkpoint

## New in v1.1: Repository Search Center
- Search text across tracked files with `git grep`
- Search commit messages across all refs
- Search tracked filenames
- Results stay inside the desktop app

## Complete capability set
Includes the v1.0 multi-repository manager and diagnostics, plus local Git operations, visual history, conflict resolution, compare/recovery, worktrees, repository health/governance, security, releases, pull requests, Actions, advanced rebase/cherry-pick/reset workflows, bundles and ZIP exports.

## Windows quick start
Extract and run `run_windows.bat`. Requires Python 3.10+ and Git. GitHub CLI is required for Releases, PRs, Actions and GitHub security APIs.

## v1.2 additions
- Pre-Commit Review Center: stage/unstage, inspect staged and unstaged diffs, run whitespace checks, flag changed files above 5 MB, and commit from one screen.
- Repository Notes: private local notes stored at `.git/gccc-notes.md` for decisions, follow-ups, current focus and release reminders.
