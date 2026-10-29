# GitHub Command Center v2.1.0

An extensible Python desktop command center for Git and GitHub. Version 2.1 is a bundled productivity, identity and release-engineering update built on the v2.0 Command Palette architecture.

## Bundled v2.1 updates
### Identity & Signing Center
- Repository-level Git name and email configuration
- Signing-key configuration and commit-signing default
- GPG secret-key inventory
- Signature inspection for recent commits
- Local signed test tag with confirmation

### Commit Message Studio
- Conventional Commit types: feat, fix, docs, refactor, perf, test, build, ci, chore and more
- Optional scope and breaking-change marker
- Body and issue/footer fields
- Live preview and clipboard copy
- Commit staged changes directly with empty-stage safeguards

### Changelog Studio
- Generate a Markdown changelog section from commits since the latest tag or chosen ref
- Categorize Conventional Commit messages into Added, Fixed, Changed, Documentation, Tests, Build/CI and Other
- Prepend a reviewed section to CHANGELOG.md
- Save or copy generated sections

### Remote Migration & Mirror Center
- Inventory remotes and refs
- Add/update a dedicated migration or backup remote
- Fetch/prune all remotes
- Deliberately mirror all refs to a dedicated remote with warning and typed confirmation
- Blocks mirror push to `origin`

## Extensible architecture
All advanced centers are searchable through Commands. New centers remain independent `tk.Toplevel` modules registered with keywords in Command Palette.

## Cumulative capability
Every feature from v0.1 through v2.0 remains included: account dashboard, local Git, graph/conflicts, advanced history operations, releases, PRs, Actions, security, health, worktrees, compare/recovery, repository portfolio management, diagnostics, smart sync, review/notes, cleanup/snapshots, patches/bisect, inspection/submodules, tasks/archive, hooks, LFS and automation recipes.

## Requirements
Python 3.10+ and Git. GitHub CLI is required for Releases, PRs, Actions and security APIs. GPG and Git LFS are optional for their respective centers.
