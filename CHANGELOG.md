# Changelog

## v3.51.0
- Added Accessibility & Display Center
- Added high-contrast and large-text preference support
- Added reduced-motion and enhanced focus-indicator preferences
- Added shared accessibility UI helpers and keyboard activation helper
- Added ACCESSIBILITY.md design baseline and tests
- Retained all v0.1-v3.50 features

## v3.50.0
- Added Public Release Readiness Center with score and JSON evidence
- Added public-release readiness service and update-policy service
- Added repository-grade SECURITY.md and CONTRIBUTING.md
- Expanded release/readiness/update/plugin test coverage
- Retained all v0.1-v3.49 features and major-version-3 decimal policy

## v3.49.0
- Added versioned plugin manifest model and validation
- Added explicit plugin permissions and executable allowlist
- Added local trusted-publisher/signature policy store
- Added SHA-256 plugin package verification
- Added canonical manifest payload and HMAC verification for local/test use
- Added Plugin Security Center and example manifest
- Added CI plugin-manifest audit and plugin security tests
- Retained all v0.1-v3.48 features

## v3.48.0
- Added recovery/reflog/reset integration tests
- Added rebase success/conflict-abort integration tests
- Added conflict index stage and resolution integration tests
- Added release tag/archive/bundle integration tests
- Added non-destructive RecoveryPolicy
- Added ReliabilityService performance probes and JSON report script
- Added CI reliability report artifact
- Retained all v0.1-v3.47 features

## v3.47.0
- Added PyInstaller Windows executable specification
- Added portable Windows ZIP builder
- Added Inno Setup installer definition
- Added SHA-256 release manifest generation and verification
- Added packaged-artifact smoke tests
- Added GitHub Actions Windows package workflow and artifact upload
- Retained all v0.1-v3.46 features

## v3.46.0
- Added task-based navigation taxonomy: Home, Changes, History, Branches, Sync, Review, GitHub, Release, Recover, Advanced
- Added reusable `ui/navigation.py` source of truth with searchable keywords
- Updated main navigation section terminology while preserving existing targets
- Added navigation model/search tests
- Retained the full Command Palette and all v0.1-v3.45 features

## v3.45.0
- Added reusable typed DiffService and unified patch parser
- Added side-by-side synchronized Visual Diff Center
- Added word-level replacement highlighting
- Added hunk staging and unstaging through cached patch apply
- Added diff unit and integration tests
- Retained all v0.1-v3.44 features

## v3.44.0
- Added Async Git Operations center powered by JobService
- Added reusable JobPanel with streaming output and cancellation
- Hardened JobService lifecycle and fixed stdout stream cleanup
- Added async center registry and tests
- Retained all v0.1-v3.43 features

## v3.43.0
- Added Windows/Linux GitHub Actions CI across Python 3.10 and 3.12
- Added compile, unittest, Ruff, Bandit, and pip-audit gates
- Added release-tag smoke workflow
- Added parser and safety-policy service modules
- Added domain registries for recovery, branch, and release centers
- Expanded automated test coverage across jobs, parsers, policies, registries, and Git helpers
- Retained all v0.1-v3.42 user-facing features

## v3.42.0
- Introduced `models/`, `services/`, `ui/`, and `centers/` package boundaries
- Added typed command and repository-state models
- Added central `GitService` and routed the legacy Git helper through it
- Added reusable cancellable `JobService`, atomic `PreferencesService`, and shared UI styles
- Added initial automated tests and `ARCHITECTURE.md`
- Retained all v0.1-v3.41 user-facing features

## v3.41.0
- Added Ref Verification Center
- Added Ignore Rule Batch Tester
- Added Fetch Preview Center
- Retained all v0.1-v3.40 functionality

## v3.40.0
- Added Show-Branch, Name-Rev and Object Growth Tracker
## v3.39.0
- Added Fixup/Squash Commits, Tracked File Flags and Revision Walk Lab
## v3.38.0
- Added Selective Stash, Worktree Move and Config Snapshot Compare
## v3.37.0
- Added Commit Message Audit, Revision Manifest and Branch Descriptions
## v3.36.0
- Added Protocol Diagnostics, Object Alternates and EOL Normalization
## v3.35.0
- Added Selective Clean, File Evolution and Remote Details
## v3.34.0
- Added Sparse Index, Maintenance Schedule and Format Inspector
## v3.33.0
- Added Lost & Found, Shallow Repository and Status Porcelain Explorer
## v3.32.0
- Added Change Statistics, Conflict Stage Explorer and Branch Rename Planner
## v3.31.0
- Added Merge Strategy Lab, Config Include Inspector and Pack Inventory
## v3.30.0
- Added Range-Diff, Refspec Lab and Git Notes Merge
## v3.29.0
- Added Git Subtree, History Rewrite Advisor and Attributes Audit
## v3.28.0
- Added Merge Commit Revert, Commit Graph/Pack Index and Diff Algorithm Lab
## v3.27.0
- Added Revert Queue, Git Log Query Builder and Index Inspector
## v3.26.0
- Added Git Replace, Merge Base and Commit Reachability
## v3.25.0
- Added Git Grep, Tree Comparison and Remote URL Audit
## v3.24.0
- Added Worktree Repair, Tag Manager Pro and Pathspec Explorer
## v3.23.0
- Added Switch & Restore, Rebase State Inspector and Git Describe
## v3.22.0
- Added Credential Redaction Audit, Ref Consistency and Release Branch Planner
## v3.21.0
- Added Dangling Object Recovery, Mailmap and Patch Identity
## v3.20.0
- Added Automated Bisect, Revision Archive and Commit Metadata
## v3.19.0
- Added Blame Explorer, Remote Prune Audit and Object Inspector
## v3.18.0
- Added Upstream Health, Release Evidence and Repository Locator
## v3.17.0
- Added Onboarding, Audit Pack and Safety Branch Manager
## v3.16.0
- Added Rules Audit, Commit Range Exporter and Branch Dashboard
## v3.15.0
- Added Pull Strategy Advisor, Detached HEAD Recovery and State Export
## v3.14.0
- Added Signature Audit, Release Comparison and Safe Branch Delete
## v3.13.0
- Added Cherry-Pick Queue, Asset Integrity and Local Release Archive
## v3.12.0
- Added Merge Preview, Reset Planner and Git Configuration
## v3.11.0
- Added Commit Templates, Patch Queue and Hook Audit
## v3.10.0
- Added Branch Protection Advisor, Favorites and Preflight Gates
## v3.9.0
- Added Force-with-Lease Safety, Advanced History Search and Bundle Inspector
## v3.8.0
- Added Stash Manager Pro, Safe Clean and Size Explorer
## v3.7.0
- Added Worktree Safety, Repository Doctor and Tag Audit
## v3.6.0
- Added rerere, remote branches, ignore/attributes and advanced clone
## v3.5.0
- Added sparse checkout, maintenance, notes and diff/merge tools
## v3.4.0
- Added interactive rebase, refs and historical browser
## v3.3.0
- Added partial staging and reflog recovery
## v3.2.0
- Major UI redesign
