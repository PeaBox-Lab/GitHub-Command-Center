# GitHub Command Center 3.78.0 Release Notes

Packaging and release-evidence hardening release.

## Blockers fixed
- Release archives are built outside their own input set using deterministic Python ZIP construction, eliminating self-inclusion.
- The 70% coverage gate is formally scoped to testable core/service/application modules; UI feature domains remain protected by architecture and UI-contract tests.

## Packaging gates
- Standard `[build-system]` and `[project]` metadata.
- `github-command-center` console entry point.
- Version consistency gate.
- ZIP integrity and generated-output exclusion gate.
- File manifest with SHA-256 per included file.
- CI wheel/sdist build and clean-install smoke test.

## Audit evidence
Release evidence includes test, architecture, security, packaging, static-audit, coverage-policy, and manifest outputs.

## Cumulative compatibility
- v3.71 developer and productivity tooling retained.
- v3.72 commit graph filters, stash diff, and conflict previews retained.
- v3.73-v3.75 architecture work retained.
- v3.76 error-handling hardening retained.
- v3.77 CI and security gates retained.
