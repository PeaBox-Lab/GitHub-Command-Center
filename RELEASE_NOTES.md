# GitHub Command Center 3.79.0 Release Notes

Release-readiness and architecture-gate hardening release.

## Improvements
- Strict shell/domain/facade architecture budgets replace obsolete legacy thresholds.
- Release readiness now verifies package version, console entry point, coverage policy, architecture/security/packaging gates, and required GitHub workflows.
- Packaging derives the artifact version from project metadata to reduce version drift.
- v3.78 deterministic ZIP, checksum, manifest, CI packaging, and audit evidence are retained.

## Cumulative compatibility
- v3.71-v3.72 developer, graph, stash, and conflict tooling retained.
- v3.73-v3.75 architecture improvements retained.
- v3.76 error handling retained.
- v3.77 CI/security gates retained.
- v3.78 packaging and evidence gates retained.
