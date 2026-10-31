
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

# Version 3.5 Addendum

## Sparse checkout
Use on large repositories when you need only selected folders. Commit or stash local changes before changing the sparse specification.

## Maintenance
Start with Refresh analysis and Auto maintenance. Normal GC is available with confirmation. Aggressive GC and reflog destruction are intentionally excluded.

## Git notes
Notes attach metadata without changing commit hashes. Notes live in a separate ref and require an explicit notes-ref push to share.

## External diff and merge tools
Install the selected tool first, then configure it for the repository. Use Difftool for comparison and Mergetool during conflicts.

# Version 3.6 Addendum

## Recorded conflict resolution
Enable rerere before recurring merge/rebase work. Autoupdate can stage reused resolutions, so review staged changes before committing.

## Remote branches
Use Remote Branch Center for explicit tracking and publishing. Remote deletion requires the exact branch name to reduce accidental server-side deletion.

## Ignore and attributes
Test a path before relying on a new ignore or attribute pattern, then review and stage the tracked configuration files.

## Advanced cloning
Use depth or blob filtering to reduce initial transfer for very large repositories. Partial and shallow clones have history/content limitations, so use a full clone when complete offline history is required.

# Version 3.7 Addendum

## Worktree Safety
Lock worktrees located on removable or intermittently mounted storage. Use Prune dry-run before removing stale worktree administration records.

## Repository Doctor
Run Doctor when a repository feels out of sync or an operation fails. Follow the specific recommended action rather than applying a generic reset.

## Tag & Release Audit
Use before releases to distinguish annotated/lightweight tags, confirm what exists on origin, and verify signatures before publishing missing tags.

# Version 3.8 Addendum

Use Stash Manager Pro to inspect a stash before applying it. Safe Clean always previews first; enabling ignored-file cleaning requires typed confirmation. Repository Size Explorer helps identify large current files before deciding whether Git LFS is appropriate.

# Version 3.9 Addendum

Use Force-with-Lease only after intentional history rewriting such as rebase or amend. Fetch first, inspect the observed upstream hash, and never use it as a routine push replacement. Advanced History Search supports Git pickaxe and regex workflows from the GUI. Verify a Git bundle before using it for recovery.

# Version 3.10 Addendum

Use Branch Protection Advisor to identify governance gaps before changing repository rules in GitHub. Favorites & Groups lets you organize PeaLang, PeaBox and other local repositories into persistent product groups. Run Preflight before pushing, opening a PR or creating a release.

# Version 3.11 Addendum

Use Commit Template Center when you want a consistent local commit structure without enforcing it on collaborators. Patch Queue is for `git format-patch` / `git am` workflows and requires a clean tree. Hook Audit lets you inspect exactly which clone-local hooks can execute before commit/push operations.

# Version 3.12 Addendum

Use Merge Preview before integrating a branch when you want to inspect the likely merge result without touching the working tree. Reset Planner always creates a recovery branch first; prefer soft or mixed reset unless discarding tracked changes is intentional. Git Configuration Center displays where each active value came from before you modify local or global settings.

# Version 3.13 Addendum

Use Cherry-Pick Queue when several non-contiguous commits must be applied in a deliberate order. The tool creates a recovery branch first. Use Asset Integrity before uploading releases, and Local Release Archive when you need a self-contained offline handover with source, full history, checksums and metadata.

# Version 3.14 Addendum

Use Signature Audit before a provenance-sensitive release. Use Release Comparison for the final tag-to-tag review. Safe Branch Delete is intentionally conservative and refuses current, worktree-active, unmerged or locally-ahead branches instead of offering force deletion.

# Version 3.15 Addendum

Use Pull Strategy Advisor after fetching when local and upstream histories differ. Rebase is protected by a backup branch; merge remains explicit. Use Detached HEAD Recovery before leaving an important detached commit. Repository State Export creates portable JSON or Markdown evidence of the current repository state.

# Version 3.16 Addendum

Use Repository Rules Audit before publishing or handing over a repository. Commit Range Exporter is useful for moving a specific development slice as patches, a bundle, or a readable Markdown inventory. Local Branch Dashboard provides branch freshness, upstream divergence, switching, comparison, and a direct route to safe branch deletion.

# Version 3.17 Addendum

Use Repository Onboarding when converting a local project into a collaboration-ready repository. Audit Pack creates portable technical evidence for handover or troubleshooting. Safety Branch Manager provides conservative cleanup of old `gccc-backup/*` branches without force deletion.

# Version 3.18 Addendum

Use Upstream Health after branch renames, repository migrations, or remote pruning. Release Evidence produces one local approval artifact before publishing. Repository Locator is useful when your workspace contains many PeaLang, PeaBox, workbench, utility, or experimental repositories nested below a common parent.

# Version 3.19 Addendum

Use Blame Explorer to find which commit introduced a specific line and immediately inspect its patch. Remote Prune Audit previews stale remote-tracking references before removing them. Git Object Inspector is a read-only advanced view of commits, trees, blobs and tags for debugging repository internals.

# Version 3.20 Addendum

Automated Bisect repeatedly executes your supplied test command while Git narrows the first bad commit. Use a deterministic command whose exit status reliably indicates good/bad behavior. Revision Archive exports any ref without changing the working tree. Commit Metadata Inspector helps distinguish author and committer data and inspect signature provenance.
