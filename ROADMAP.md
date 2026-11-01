# GitHub Command Center Roadmap

## Completed through v3.59

- Central GitService, JobService, typed models and shared UI architecture
- 100+ automated tests and real Git integration tests
- Visual diff and selected-hunk stage/unstage
- Task-based navigation and accessibility preferences
- Windows packaging, validation and UI-regression workflows
- Plugin manifest security, executable allowlists and publisher trust
- Public release readiness and reliability/startup evidence
- Extracted Changes, History, Review, Branches, Recovery, Release, Sync, Backup and GitHub centers
- Legacy duplicate retirement for twelve migrated center classes
- Architecture CI gate preventing renewed monolith/synchronous-call growth

## v3.60 stabilization milestone

- Migrate/extract submodule, Git LFS and clone workflows
- Reduce remaining heavy synchronous call sites below 20
- Remove remaining duplicate compatibility classes where extracted replacements exist
- Make Windows validation/UI matrix prerequisites for package publishing
- Add verified updater metadata/download/checksum flow
- Add Authenticode signing hooks and signature-verification gates
- Performance/accessibility regression pass on packaged Windows artifacts

## Post-v3.60

- Continue lowering `local_git_gui.py` line/class budgets each release
- Certificate-backed plugin signatures and revocation/transparency support
- Provider adapters only after GitHub workflows remain stable
- No new feature center may be implemented in `local_git_gui.py`
