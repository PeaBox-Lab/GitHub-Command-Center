# GitHub Command Center v3.76.0

> A unified Python desktop command center for Git, GitHub, repository engineering, recovery, releases and developer workflows.

Version **3.71.0 is an incremental upgrade of v3.70.0**. It preserves the complete v3.70 application and adds developer-facing Ref Compare and Revision Explain tools. No scratch rebuild or feature reset is used for this release.

## Highlights

- Full cumulative Git and GitHub feature set from v3.70 retained
- Workspace UX with nine user-oriented task areas
- Home Dashboard and Universal Search
- Visual Diff, partial staging and pre-commit review
- Branch, tag, stash, worktree, submodule and Git LFS management
- Interactive rebase, cherry-pick, bisect, reflog and recovery tooling
- Pull requests, GitHub Actions, releases and security workflows
- Repository health, metrics, insights and developer quality checks
- Windows packaging, validation and UI regression infrastructure
- Verified-update foundation and plugin-security controls

## New in v3.71

### Ref Compare
Compare two refs, tags, branches or commits using:

- left/right commit history
- graphical one-line history
- diff statistics
- changed-file status

### Revision Explain
Explain any Git revision using:

- `git rev-parse --verify`
- `git cat-file -t`
- `git name-rev`
- full commit metadata

Both tools are read-only and live under the extracted developer-tooling architecture.

## Developer tooling

The cumulative developer suite now includes:

- Developer Toolbox
- Git Object Query
- Developer Quality
- Code Search
- Patch Series
- Repository Metrics
- Build & Validation Runner
- Developer Artifacts
- Ref Compare
- Revision Explain

## Everyday workflow

Use the simplified workspace groups:

1. Changes
2. History
3. Branches
4. Sync
5. Review
6. GitHub
7. Release
8. Recover
9. Advanced

Press **Ctrl+K** for the complete specialist toolset.

## Safety principles

- No `shell=True` command execution
- GitHub workflows use asynchronous/background execution where migrated
- Destructive workflows use confirmations and recovery controls
- Safety branches are created before selected history-rewriting operations
- Force operations prefer `--force-with-lease`
- Recovery favors reflog/recovery branches and verified backups before destructive resets

## Windows

Run from source with `run_windows.bat`, or use the packaging infrastructure for:

- PyInstaller executable
- Portable ZIP
- Inno Setup installer
- SHA-256 checksums
- Windows validation
- UI regression testing
- Optional Authenticode signing hooks

## Requirements

- Python 3.10+
- Git
- Tkinter
- GitHub CLI (`gh`) for GitHub-hosted workflows
- Optional Git LFS, GPG, Ruff, Bandit and pip-audit for their associated centers

## Run from source

```bash
python app.py
```

## Validation

```bash
python -m compileall -q .
python -m unittest discover -s tests -v
python scripts/architecture_gate.py
```

## Documentation policy

Every release must update at least:

- `README.md`
- `CHANGELOG.md`
- `RELEASE_NOTES.md`
- `USER_GUIDE.md`

`ROADMAP.md` and architecture/security documentation are updated whenever the corresponding scope changes.

## v3.71 Git productivity additions

- **Git Log Visualizer**: searchable branch-aware graph, ref decorations, commit inspection, and selected-commit comparison to HEAD.
- **Stash Workbench**: create, preview, selectively stash paths, apply, pop, branch, and drop stashes with background mutation jobs.
- **Worktree Workbench**: inventory, add, lock/unlock, move, remove, dry-run prune, and prune linked worktrees.
- **Ref Compare** and **Revision Explain** remain available from the v3.71 developer tooling.

Existing Git, GitHub, release, recovery, developer, accessibility, packaging, and validation functionality from v3.70 is retained.

## Release lineage

v3.72.0 is built directly from the complete v3.71.0 release.


## New in v3.76

- Eliminated all bare `except:` handlers across the application package.
- Eliminated direct `except Exception` handlers and replaced them with a documented typed recoverable-error boundary.
- Added structured error logging through `core/error_boundary.py`.
- Ensured `KeyboardInterrupt`, `SystemExit`, and other `BaseException` control-flow signals are not swallowed.
- Added automated AST-based error-handling gates to prevent regression.
- Preserved all cumulative Git, GitHub, recovery, release, developer, graph, stash, worktree, accessibility, and compatibility functionality.

## New in v3.72
- Interactive Commit Graph filters by refs, author, dates, message, path, merges and first-parent history.
- Stash Diff & Conflict Preview uses read-only `git merge-tree` analysis before apply/pop.
- Complete v3.71 stash, worktree, log, developer, GitHub, recovery and release functionality is retained.

