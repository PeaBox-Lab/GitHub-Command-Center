
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

# Version 3.21 Addendum

Use Dangling Object Recovery only after ordinary Reflog Recovery cannot find the desired commit. Creating a recovery branch is non-destructive and prevents the selected unreachable commit from later garbage collection. Commit `.mailmap` when canonical contributor identities should be shared. Patch Identity Comparator is useful when determining whether a rebased or cherry-picked commit already contains the same logical change.

# Version 3.22 Addendum

Credential Redaction Audit intentionally hides matching values in its report. Treat findings as review signals and rotate any credential confirmed to be exposed. Ref Consistency is useful after manual ref changes, repository restoration, or remote migration. Release Branch Planner provides a clean, explicit start point for release stabilization work.

# Version 3.23 Addendum

Use Switch & Restore when you want modern `git switch`/`git restore` semantics instead of legacy checkout behavior. Rebase State Inspector is useful whenever an interactive or normal rebase pauses and you need to understand exactly what Git expects next. Git Describe provides reproducible human-readable version strings for packaging and diagnostics.

# Version 3.24 Addendum

Use Worktree Repair after moving a linked worktree folder or restoring repository metadata. Tag Manager Pro centralizes annotated/signed tag lifecycle operations and keeps remote deletion behind typed confirmation. Pathspec Explorer is a safe way to test complex Git file-selection expressions before using them in staging, status, diff, or automation workflows.

# Version 3.25 Addendum

Git Grep Studio searches tracked repository content and can search an older tree without checking it out. Tree Comparison provides a compact structural view of changes between refs. Remote URL Audit is useful when fetching from an upstream repository while pushing to your fork under a different URL.

# Version 3.26 Addendum

Git Replace is an advanced local object-interpretation mechanism and should be used deliberately because other collaborators will not see replace refs automatically. Merge Base Explorer helps explain histories before merge/rebase decisions. Commit Reachability Explorer is useful when determining whether a fix is already included in release tags or long-lived branches.

# Version 3.27 Addendum

Use Revert Queue to undo multiple non-merge commits while retaining public history; it creates ordinary revert commits and a safety branch. Git Log Query Builder makes targeted audit/history reports easier. Index Inspector exposes the staging area's actual objects and conflict stages, which is especially useful during complex merges.

# Version 3.28 Addendum

Reverting a merge commit requires choosing the mainline parent that represents the history to retain; inspect and preview before execution. Commit Graph & Pack Index improves performance for large repositories without rewriting commits. Diff Algorithm Lab helps choose clearer output for refactors, moved blocks, or noisy diffs.

# Version 3.29 Addendum

Use Git Subtree when you want to vendor another repository without requiring submodule initialization. History Rewrite Advisor deliberately generates commands rather than running them; execute history rewrites only in a disposable backed-up clone and coordinate with collaborators. Attributes Audit helps verify that binary, text, diff, merge, EOL, and LFS rules are taking effect as intended.

# Version 3.30 Addendum

Use Range-Diff after an interactive rebase to validate that the rewritten patch series still represents the intended changes. Refspec Lab provides dry runs before you persist unusual fetch/push mappings. Notes Merge supports combining independent metadata refs without rewriting the underlying commits.

# Version 3.31 Addendum

Use Merge Strategy Lab when the default merge result needs comparison against another strategy or strategy option. Config Include Inspector helps troubleshoot unexpected Git behavior caused by conditional user/worktree configuration. Pack Inventory is read-only and helps identify historical storage hotspots before using the separate History Rewrite Advisor.

# Version 3.32 Addendum

Change Statistics helps quantify the review surface of a release or branch range. Conflict Stage Explorer exposes the index's true base/ours/theirs blobs for difficult merges. Branch Rename Planner coordinates local rename, new upstream publication, and optional old remote deletion with explicit safeguards.

# Version 3.33 Addendum

Use Lost & Found Center after refs and reflogs no longer expose a desired commit; create a branch immediately to protect a recovered commit from future garbage collection. Shallow Repository Center controls how much history a shallow clone has locally. Status Porcelain Explorer helps troubleshoot automation by exposing Git's stable v2 status records.

# Version 3.34 Addendum

Sparse Index can reduce index overhead in very large sparse-checkout repositories, but should be enabled only with a compatible Git version and a clean tree. Maintenance Schedule controls Git's registered background maintenance. Repository Format Inspector is read-only because changing object/ref formats can break compatibility with older Git clients and tooling.

# Version 3.35 Addendum

Selective Clean is safer than a broad repository clean because you choose exact previewed paths. File Evolution provides a focused historical view of one tracked file and supports historical export. Remote Details exposes Git's own remote/tracking assessment, with both live and cached modes.

# Version 3.36 Addendum

Protocol Diagnostics helps troubleshoot remote capability negotiation and Git protocol v2 behavior without changing refs. Object Alternates Inspector is useful for shared/reference clones; dissociation may require significant disk space. EOL Normalization should be done from a clean tree and committed separately from functional code changes.

# Version 3.37 Addendum

Commit Message Audit is useful before release-note automation and when improving Conventional Commit consistency. Revision Manifest provides a source-tree integrity record independent of ZIP timestamps. Branch descriptions are clone-local notes for branch purpose and are not a substitute for shared documentation or pull-request context.

# Version 3.38 Addendum

Selective Stash is useful when only certain files should be put aside while other work remains visible. Worktree Move relocates linked worktrees only after checking their cleanliness. Config Snapshot Compare helps investigate unexpected Git behavior after identity, includeIf, credential-helper, or workflow configuration changes; review the report before sharing because Git config can contain sensitive values.

# Version 3.39 Addendum

Use Fixup/Squash Commit Center when preparing staged corrections for an autosquash rebase. Tracked File Flags are clone-local index behavior and should not replace `.gitignore` or `.gitattributes`. Revision Walk Lab helps explain why particular commits appear in release, merge, and ancestry analyses.

# Version 3.40 Addendum

Show-Branch Explorer gives a compact multi-tip topology view that complements the graphical log. Name-Rev translates raw object IDs into understandable branch/tag-relative names. Object Growth Tracker helps determine whether maintenance, generated artifacts, or repository history are increasing local object storage over time.

# Version 3.41 Addendum

Ref Verification is useful before resets, tag operations, scripts, or recovery actions where an ambiguous ref would be risky. Ignore Rule Batch Tester explains exactly why each path is or is not ignored. Fetch Preview should be used when a remote/refspec may delete or force-update remote-tracking refs and you want to inspect Git's dry-run first.


# Version 3.42 Addendum

Existing tools remain available through the same workspace and Command Palette. Contributors should run `python -m unittest discover -s tests -v` and follow `ARCHITECTURE.md`.


# Version 3.43 Addendum

CI workflows now validate Windows/Linux and Python 3.10/3.12. Contributors should run `python -m unittest discover -s tests -v` before push; GitHub Actions additionally runs Ruff, Bandit, and pip-audit.


# Version 3.44 Addendum

Use **Ctrl+K > Async Git Operations** for long-running fetch, fsck, maintenance, gc, commit-graph, and tag-fetch jobs. Output streams live and active jobs can be cancelled.


# Version 3.45 Addendum

Open **Ctrl+K > Visual Diff Center**. Choose Working tree or Staged, select a file and hunk, review side-by-side/word-level changes, then stage or unstage the selected hunk.


# Version 3.46 Addendum

Navigation is now task-oriented. Start in Changes for daily commit work, Sync for network/upstream operations, Review before PRs, Release for publication, Recover for repair workflows, and Advanced for specialized Git plumbing. Ctrl+K still searches the entire toolset.


# Version 3.47 Addendum

Windows distributions can now be produced as a standalone EXE, portable ZIP, or installer. Verify `SHA256SUMS.txt` before deployment. Source launchers remain available for development.


# Version 3.48 Addendum

No major workflow was removed. Reliability work strengthens recovery, rebase, conflict, release, archive and bundle behavior through real Git repositories created during tests. CI also records reliability evidence for each platform/Python combination.


# Version 3.49 Addendum

Open **Ctrl+K > Plugin Security Center** before enabling a command plugin. Review the executable, permissions, publisher, signature policy, and SHA-256 result. Auditing never runs the plugin.


# Version 3.50 Addendum

Before publishing a release, open **Ctrl+K > Public Release Readiness**. Resolve required FAIL items, export the JSON evidence, then continue through Preflight, Release Evidence, Asset Integrity, and Release Center.
