# GitHub Command Center v0.2.0

Python desktop replacement for common GitHub web and TortoiseGit tasks.

## Local Git workspace
Clone or initialize repositories; inspect status; stage selected/all files; unstage; commit; fetch; fast-forward pull; push; inspect diffs and 100 recent commits; create, switch, merge and delete branches; abort merges; save/pop stashes; create/delete/push tags; view/edit remotes; list conflicts; preview and clean untracked files; discard tracked changes; open the local folder.

Destructive operations are confirmed. Pull uses `--ff-only` to avoid accidental merge commits.

## GitHub account features
Dashboard, statistics, repository search, activity, insights, repository and issue creation, cloning, API allowance, and optional OS-keyring token storage.

## Windows
Extract and double-click `run_windows.bat`. Requires Python 3.10+ and Git on PATH.

## v0.3 visual tools
Use **Visual history** in Local Git for a color-coded branch/merge topology graph covering up to 250 commits. Use **Resolve conflicts** for a three-pane ours/merged/theirs editor, one-click side selection, manual editing, staged resolution, and merge abort.
