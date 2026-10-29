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

## v1.3 additions
- **Branch Cleanup Center:** inventories local branches, merged state, last-commit date, upstream and worktree usage. It only permits normal `git branch -d` deletion for branches already merged into the current branch, while protecting the current branch and branches checked out in worktrees.
- **Project Snapshot:** generates an exportable Markdown handover containing branch/status, recent commits, tags, remotes, detected project documentation and private repository notes.

## v1.4 additions
- **Patch Center:** export working-tree or staged changes as `.patch`, generate a `git format-patch` commit series, inspect patch contents, run `git apply --check`, apply a validated patch, or apply email-style patch series using `git am`.
- **Regression Finder:** guided `git bisect` UI with known good/bad refs, Good/Bad/Skip decisions and reset. It requires a clean working tree before starting.

## v1.5 additions
- **Commit Inspector & File History:** inspect up to 150 commits, view complete commit patches/statistics, follow the history of a specific file across renames, and run line-level `git blame` from the GUI.
- **Submodule Center:** inventory recursive submodule states, add a submodule, initialize/update recursively, synchronize configured URLs, and explicitly update submodules from their configured remote branches.

## v1.6 additions
- **Repository Task Center:** local-only per-repository checklist stored under `.git/gccc-tasks.txt`, with add, complete/reopen, multi-delete and save workflows.
- **Archive & Handover Center:** one place for clean HEAD ZIP export, full-history Git bundle creation, Project Snapshot handover, and a diagnostic support pack containing status, remotes, recent commits, configuration and `git fsck` results.
