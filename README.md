# GitHub Command Center

> **A unified Python desktop command center for Git and GitHub workflows.**

GitHub Command Center is a Python-based desktop application designed to make Git and GitHub easier to use without relying on complex context menus, command-line memorization, or repeatedly opening GitHub in a browser.

It combines everyday Git operations, advanced source-control workflows, GitHub integration, repository security, release engineering, recovery tools, and multi-repository management into one graphical interface.

---

## Overview

GitHub Command Center is intended as a user-friendly alternative to fragmented Git workflows across tools such as:

- Git command line
- TortoiseGit
- GitHub web interface
- GitHub CLI
- Multiple standalone Git utilities

The goal is not to replace Git.

The goal is to provide a safer and easier graphical layer over Git and GitHub operations while still exposing the underlying Git concepts and command results.

---

# Key Features

## Modern Git Workspace

A consolidated desktop workspace for everyday Git activity.

- Clone repositories
- Initialize repositories
- View working-tree status
- Stage selected files
- Stage all changes
- Unstage changes
- Commit
- Fetch
- Pull
- Push
- View diffs
- Discard selected changes
- Clean untracked files safely
- Open repository folders
- Configure remotes

---

## Partial Staging

Stage only the changes you actually want to commit.

- Inspect individual diff hunks
- Stage one hunk at a time
- Unstage individual staged hunks
- Preview patches before staging
- Stage or unstage the complete file when required

Useful for splitting unrelated changes into clean, focused commits.

---

## Visual Commit History

Explore repository history graphically.

- Colored branch lanes
- Commit nodes
- Merge relationships
- Branch and tag references
- Commit hash
- Author
- Date
- Commit subject
- Historical checkout with confirmation

---

## Repository History Browser

Browse the repository exactly as it existed at an earlier revision.

- Browse HEAD
- Browse branches
- Browse tags
- Browse commit hashes
- Navigate historical folders
- Read historical files without checkout
- Export historical files
- Inspect historical repository structure

---

## Commit Inspector

Investigate repository history in detail.

- Recent commit history
- Full commit patches
- Commit statistics
- Rename-aware file history
- `git blame`
- Line-level author attribution
- Commit dates and messages

---

# Branch Management

Manage branch workflows directly from the GUI.

- Create branches
- Switch branches
- Merge branches
- Rename branches
- Delete merged branches
- Track remote branches
- Publish local branches
- Compare branches
- View ahead/behind status
- Detect branches in active worktrees

---

## Safe Branch Delete

Branch deletion is intentionally conservative.

Before deletion, GitHub Command Center checks:

- Is this the current branch?
- Is it being used by a worktree?
- Has Git reported it as merged?
- Does it contain commits ahead of its upstream?

Normal:

```bash
git branch -d
```

is used.

Force deletion is intentionally not offered in the safe-delete workflow.

---

# Interactive Rebase

A graphical editor for interactive rebase.

Supported actions:

```text
pick
reword
edit
squash
fixup
drop
```

Features include:

- Reorder commits
- Change rebase action
- Inspect commits before rewriting
- Clean-working-tree validation
- Automatic safety branch
- Continue
- Skip
- Abort

Before rewriting history, a recovery branch is automatically created:

```text
gccc-backup/pre-rebase-YYYYMMDD-HHMMSS
```

---

# Cherry-Pick

Support for both individual and multi-commit workflows.

## Cherry-Pick Queue

- Browse available commits
- Add commits to a queue
- Reorder commits
- Remove commits
- Apply commits sequentially
- Continue after conflict resolution
- Abort the operation

A recovery branch is created before executing the queue.

---

# Merge Tools

## Merge Preview

Preview a merge before changing the working tree.

Uses Git merge-tree functionality to inspect the likely result.

- Calculate merge base
- Inspect potential integration
- Perform the merge explicitly
- Abort a merge

---

## Merge Conflict Resolver

Three-pane graphical conflict resolution:

```text
OURS           MERGED RESULT           THEIRS
```

Features:

- View current-branch version
- View incoming version
- Edit merged result
- Use ours
- Use theirs
- Save resolution
- Stage resolved files
- Move to the next conflict
- Abort merge

---

## Recorded Conflict Resolution

Git `rerere` support enables previous conflict resolutions to be reused.

- Enable rerere
- Enable rerere autoupdate
- Inspect remaining conflicts
- Reuse recorded resolution
- Forget a resolution
- Clear resolution cache

---

# Reflog Recovery

Recover commits after operations such as:

- Reset
- Rebase
- Branch deletion
- Checkout
- Detached HEAD work

The Reflog Recovery Center provides:

- Reflog entry
- Commit hash
- Timestamp
- Git action
- Message
- Commit inspection

The recommended recovery method is to create a new branch at the selected commit instead of immediately resetting an existing branch.

Example:

```text
recovery/20261030-001000-a1b2c3d
```

---

# Reset & Recovery

Protected reset workflows support:

- Soft reset
- Mixed reset
- Hard reset

Before reset, GitHub Command Center automatically creates:

```text
gccc-backup/pre-reset-YYYYMMDD-HHMMSS
```

Hard reset additionally requires typed confirmation.

---

# Detached HEAD Recovery

Detect and recover detached work safely.

- Detect detached HEAD
- Show exact commit
- Inspect current commit metadata
- Create a branch at the detached commit
- Return to the repository's normal default branch

---

# Stash Manager

Advanced stash management includes:

- Named stashes
- Include untracked files
- Preview stash patches
- Apply
- Pop
- Drop
- Create a new branch from a stash

---

# Unified Ref Browser

One interface for repository references:

- Local branches
- Remote branches
- Tags
- Stash
- Git notes
- Other refs

Features include:

- Search refs
- Inspect associated commits
- Create branches from refs
- Switch branches
- Detached checkout
- Copy ref names

---

# Worktrees

Manage multiple development workspaces from one repository.

- List worktrees
- Create worktrees
- Create branch + worktree
- Remove secondary worktrees
- Lock worktrees
- Unlock worktrees
- Preview stale-worktree pruning
- Prune stale metadata

---

# Sparse Checkout

Useful for large monorepositories.

- Enable cone-mode sparse checkout
- Select folders to materialize
- Add sparse paths
- View sparse configuration
- Restore the complete working tree

---

# Advanced Clone Wizard

Clone repositories with advanced Git options.

Supported workflows:

- Full clone
- Shallow clone
- Specific depth
- Specific branch
- Single branch
- No checkout
- Partial clone

Example partial clone:

```bash
git clone --filter=blob:none
```

Also supports recursive submodules.

---

# Submodules

- List recursive submodules
- Add submodules
- Initialize submodules
- Update recursively
- Update from configured remote branches
- Synchronize submodule URLs

---

# Git LFS

Integrated Git LFS management.

- Inspect LFS environment
- View tracked patterns
- Track new patterns
- Untrack patterns
- View LFS files
- Pull LFS objects
- Prune old local LFS objects

Example:

```text
*.zip
*.exe
*.bin
```

---

# Git Notes

Attach metadata to commits without changing their hashes.

- View notes
- Add notes
- Replace notes
- Delete notes
- Custom notes refs
- Explicitly push notes to origin

Useful for:

- Review annotations
- Audit information
- Release metadata
- Internal engineering notes

---

# Git Hooks

## Hooks Manager

Manage local repository hooks such as:

```text
pre-commit
commit-msg
pre-push
```

Features:

- Edit hook source
- Enable
- Disable
- Test hooks
- Built-in safe templates

## Hook Audit

Audit local executable hooks:

- Hook name
- Executable state
- File size
- Modification timestamp
- Source preview

---

# GitHub Integration

GitHub Command Center also integrates GitHub-hosted workflows.

## Repository Dashboard

- Repository statistics
- Stars
- Forks
- Issues
- Repository visibility
- Languages
- Recent activity
- Repository health insights

---

## Issues

- Create issues
- View issue-related repository activity

---

## Pull Requests

- List pull requests
- Open
- Closed
- Merged
- Draft
- Inspect PR details
- Create PRs
- Checkout PRs
- Merge PRs

Supported merge strategies:

```text
merge
squash
rebase
```

---

# GitHub Actions

Integrated CI/CD monitoring.

- View workflow runs
- Workflow name
- Branch
- Event
- Status
- Result
- View workflow logs
- Re-run workflows
- Cancel workflows
- Manually dispatch workflows

---

# Releases

## Release Center

- Release-readiness checks
- Generate release notes
- Create annotated tags
- Push tags
- Publish GitHub releases
- Draft releases
- Pre-releases
- Attach multiple release assets

---

## Release Comparison

Compare two tags or refs.

- Number of commits
- Diff statistics
- Commit inventory
- Changed-file inventory
- Markdown export

---

## Release Asset Integrity

Generate and verify:

```text
SHA256SUMS.txt
```

Supports:

- SHA-256 generation
- PASS
- FAIL
- MISSING
- Invalid manifest detection

---

## Local Release Archive

Create an offline release package containing:

```text
project-version-source.zip
project-version.bundle
RELEASE_NOTES.md
SHA256SUMS.txt
release-metadata.json
```

This provides both clean source and recoverable Git history.

---

# Repository Security

## Security & Dependency Center

GitHub-backed security views include:

- Dependabot alerts
- Code-scanning alerts
- Secret-scanning alerts

Local checks include:

- Potentially sensitive tracked filenames
- Large tracked files
- Git object integrity
- Optional `pip-audit`
- Optional Bandit analysis
- SHA-256 generation

---

# Branch Protection Advisor

Inspect GitHub branch-protection settings.

- Required PR reviews
- Required approval count
- Dismiss stale reviews
- Required status checks
- Admin enforcement
- Force-push protection
- Branch-deletion protection

The advisor is read-only by design.

---

# Repository Doctor

Diagnose common repository problems.

Checks include:

- Working-tree state
- Current branch
- Upstream
- Origin
- Object integrity
- Merge conflicts
- Ahead/behind divergence

Each problem includes a recommended next action.

---

# Repository Health

A repository-health score evaluates:

- README
- LICENSE
- CHANGELOG
- SECURITY
- CONTRIBUTING
- CODEOWNERS
- Issue templates
- PR template
- `.gitignore`
- `.gitattributes`
- CI workflows
- Tests
- Version tags
- Working-tree cleanliness

---

# Repository Rules Audit

Audit repository engineering controls before release or handover.

Includes:

- Documentation
- Governance
- CI
- CODEOWNERS
- Upstream configuration
- Branch attachment

Outputs:

```text
PASS
REVIEW REQUIRED
```

---

# Preflight Quality Gates

Before push, PR, or release:

- Clean working tree
- Git whitespace validation
- Python syntax compilation
- Git object integrity

Result:

```text
PASS
FAIL
```

Reports can be exported.

---

# Commit Signing & Provenance

## Identity & Signing

- Repository Git name
- Repository email
- Signing key
- Default commit signing
- GPG key inventory
- Signature verification

## Signature Audit

Audit large ranges of commits for:

- Valid signatures
- Invalid signatures
- Expired signatures
- Revoked keys
- Unknown trust
- Unsigned commits

---

# Repository Maintenance

- Git object statistics
- `git maintenance run --auto`
- Normal `git gc`
- Full `git fsck`
- Commit graph generation
- Scheduled-maintenance registration

Aggressive garbage collection and automatic reflog destruction are deliberately excluded.

---

# Repository Size Explorer

- Approximate working-tree size
- `.git` directory size
- Git object statistics
- Tracked-file count
- Largest tracked files

Useful for identifying Git LFS candidates.

---

# Safe Clean

Cleanup operations always begin with a dry run.

- Preview untracked content
- Include directories optionally
- Ignored content excluded by default

Cleaning ignored content requires typing:

```text
CLEAN IGNORED
```

---

# Advanced History Search

Search repository history using:

## Commit message search

```bash
git log --grep
```

## Pickaxe

```bash
git log -S
```

Find commits where the number of occurrences of specific text changed.

## Diff regex

```bash
git log -G
```

## File history

```bash
git log --follow
```

---

# Force-with-Lease Safety

For intentionally rewritten history.

The GUI supports:

```bash
git push --force-with-lease
```

It deliberately does **not** expose plain:

```bash
git push --force
```

Safeguards include:

- Fetch first
- Show observed upstream commit
- Show local HEAD
- Show ahead/behind counts
- Typed branch-name confirmation
- Final confirmation
- Detached HEAD protection

---

# Repository Backup & Recovery

## Git Bundles

Create complete repository backups.

```bash
git bundle create project.bundle --all
```

Functions include:

- Create bundle
- Verify bundle
- List refs
- Clone from bundle

---

## Project Snapshot

Generate a portable Markdown handover containing:

- Branch
- Working-tree state
- Recent commits
- Tags
- Remotes
- Documentation inventory
- Local repository notes

---

# Multi-Repository Management

## Repository Manager

Scan a workspace and view:

- Repository
- Branch
- Clean/changed state
- Ahead/behind
- Origin URL

Perform multi-repository fetch operations.

## Batch Operations

Run selected operations across repositories:

- Fetch/prune
- Status
- Integrity checks
- Python compilation
- FF-only pull

No force operations are used.

---

# Favorites & Groups

Organize local repositories by product or purpose.

Examples:

```text
PeaLang
PeaBox
Data Workbench
Utilities
Experiments
```

Favorites are stored under:

```text
~/.gccc-favorites.json
```

---

# Portfolio History

Capture repository-state snapshots in local SQLite:

```text
~/.gccc-portfolio.sqlite3
```

Records include:

- Timestamp
- Repository
- Branch
- Clean/changed
- Ahead
- Behind

History can be exported to CSV.

---

# Repository State Export

Export repository state as:

```text
JSON
Markdown
```

Includes:

- Repository
- Path
- Branch
- HEAD
- Upstream
- Changes
- Remotes
- Tags
- Recent commits

---

# Commit Range Export

Transfer a selected development slice.

Given:

```text
base..tip
```

export as:

- `git format-patch`
- Git bundle
- Markdown commit inventory

---

# Automation

## Automation Recipes

Repository-local automation definitions stored under:

```text
.git/gccc-recipes.json
```

Built-in recipes include:

- Python compilation
- Git integrity
- Whitespace checking

---

## Plugin Manager

JSON command plugins stored under:

```text
.git/gccc-plugins/
```

Example:

```json
{
  "name": "Run project tests",
  "description": "Local test command",
  "command": ["python", "-m", "pytest", "-q"],
  "enabled": true
}
```

Commands are executed as argument arrays without shell interpolation.

Plugins still execute with the user's permissions and should always be reviewed before execution.

---

# Background Jobs

- Queue commands
- Run without freezing the UI
- Live status
- Output logs
- Exit codes
- Cancel active processes
- Clear completed jobs

---

# Command Palette

Press:

```text
Ctrl+K
```

Search for features using keywords such as:

```text
rebase
conflict
release
reflog
security
LFS
stash
bundle
worktree
partial staging
history
doctor
```

This keeps the main interface uncluttered even as functionality expands.

---

# Keyboard Shortcuts

```text
Ctrl+K       Command Palette
F5           Refresh repository
Ctrl+Enter   Commit workflow
```

Double-click a changed file to inspect its diff.

---

# Safety Philosophy

Powerful Git commands should not be dangerous simply because they are accessible through a GUI.

GitHub Command Center therefore prefers:

- Fast-forward-only pulling
- `--force-with-lease`, never plain force push
- Recovery branches before history rewriting
- Dry-run before cleaning
- Normal branch deletion instead of force deletion
- Reflog-based recovery
- Explicit server-side deletion confirmation
- Clean-tree gates before risky operations
- Git bundle backups
- Visible command output

Typical safety branches:

```text
gccc-backup/pre-rebase-...
gccc-backup/pre-reset-...
gccc-backup/pre-cherry-pick-...
gccc-backup/pre-pull-rebase-...
```

---

# Requirements

## Core

- Python 3.10+
- Git
- Tkinter

## Optional

### GitHub CLI

Required for functionality such as:

- Pull Requests
- GitHub Actions
- GitHub Releases
- GitHub security APIs
- Authentication status

Authenticate using:

```bash
gh auth login
```

### Git LFS

Required for Git LFS Center.

### GPG

Required for GPG signing workflows.

### Security scanners

Optional:

```bash
python -m pip install pip-audit bandit
```

---

# Running on Windows

Extract the package and run:

```text
run_windows.bat
```

The launcher creates a local Python virtual environment when required.

---

# Running on Linux

```bash
./run_linux.sh
```

Tkinter may need the operating-system package, for example:

```bash
sudo apt install python3-tk

---

# Roadmap

Planned areas include:

- Richer line-level staging
- Better side-by-side and word-level diffs
- Image comparison
- Improved large-repository workflows
- More visual metrics and charts
- Stronger automated testing
- Modular `centers/` architecture
- Installer packaging
- Windows executable signing
- Plugin signing and allowlists
- OAuth / GitHub App authentication
- GitLab integration
- Azure DevOps integration
- Team policy bundles

---

# License

A permissive open-source license such as the **MIT License** is recommended if the project is intended for public distribution.

---

# Project Philosophy

**GitHub Command Center is not another Git implementation.**

It uses Git as the source-control engine and adds a graphical workflow layer focused on:

1. Discoverability
2. Safety
3. Visual workflows
4. GitHub integration
5. Repository health
6. Release engineering
7. Recovery
8. Multi-repository productivity
9. Extensibility
10. Clear visibility into what Git is actually doing

> **Git and GitHub without the context-menu maze.**
