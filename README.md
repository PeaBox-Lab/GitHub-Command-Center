# GitHub Command Center v3.58.0

Version 3.58 consolidates the v3.50-v3.60 hardening roadmap: architecture extraction, async Git/GitHub execution, review/release separation, Windows UI regression, packaging, accessibility, reliability, plugin security and readiness evidence.

## New extracted centers
- Review Center V2: changed-file review plus async tests, compile, Ruff and Bandit
- Release Publish Center V2: annotated tags, async tag push and async GitHub Release creation
- GitHub Workflow Center: PR checks/merge, workflow dispatch, issue creation and failed-run rerun through JobService

## Remaining GitHub workflows migrated async
All added GitHub mutation workflows use `gh` argument arrays and `JobPanel`; no shell execution is used.

## Windows UI regression
The Windows matrix creates real Changes, History, Review and Release Evidence windows at 1366x768 and 1920x1080 with 100%, 125% and 150% scaling, inspects tables for narrow columns/multiline spillover and uploads `ui-regression.json`.

## Roadmap consolidation
Completed foundations from v3.50-v3.60 include 100+ tests, public readiness, accessibility, Windows packaging/validation, visual diff, task navigation, JobService, plugin security, startup profiling, table-layout correction and staged center extraction. Next releases should prioritize updater/signing and removing duplicated legacy class bodies.
