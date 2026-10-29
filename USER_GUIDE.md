# GitHub Command Center 3.1 User Guide

## Background Jobs
Open Commands > Background Jobs, enter a command, and queue it. Select a job to inspect live output. Cancellation terminates the process but cannot undo work already completed by that process.

## Preferences
Preferences are stored under your home directory rather than a repository. Theme is applied immediately; other values establish defaults for ongoing modularization.

## Portfolio History
Capture a snapshot from the parent workspace whenever you want a point-in-time view of repository cleanliness and upstream divergence. Export CSV for Excel, Power BI or Python analysis.

## Self-Test
Run Self-Test after installation, environment changes or upgrades. A PASS confirms core command and parser readiness, not correctness of every external GitHub permission.

All earlier centers remain searchable through Commands.

# Version 3.2 UI Guide

Use the top action bar for daily Git tasks. Use the left navigation for common work, collaboration and quality centers. Press Ctrl+K for the complete searchable feature list. The badges above the working tree show the current branch, number of changed entries and upstream divergence.

Keyboard shortcuts: Ctrl+K opens Commands, F5 refreshes, and Ctrl+Enter opens commit entry.

# Version 3.3 Addendum

## Partial staging
Open Partial staging, select a changed text file, then select and preview a hunk. Stage selected hunk adds only that patch to the index. To reverse one staged hunk, choose Unstage selected hunk and select it in the staged-hunk dialog. Use whole-file actions for new binary files or patches that Git cannot apply independently.

## Reflog recovery
Open Reflog recovery after an accidental reset, rebase, branch deletion or checkout. Inspect the candidate commit, then create a recovery branch. This is safer than immediately resetting the current branch. Detached checkout is available for inspection, but branch creation is recommended for permanent recovery.

# Version 3.4 Addendum

## Interactive rebase
Start with a clean working tree. Enter the parent/base before the commits to edit, load the plan, reorder commits and assign actions. The app creates a backup branch before execution. If rebase pauses, resolve conflicts and use Continue, Skip or Abort.

## Unified refs
Use All refs to search local and remote branches, tags, stash and notes. Deletion remains intentionally limited to normal local branch deletion and local tags.

## Historical repository browser
Choose a recent commit or enter a ref. Expand directories to inspect the tree, select a text file to view it, or export any historical blob without checking it out.
