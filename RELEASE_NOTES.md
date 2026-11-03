# GitHub Command Center 3.77.0 Release Notes

CI and security-gate hardening release.

## CI
- Test matrix: Ubuntu and Windows on Python 3.10, 3.11, 3.12, and 3.13.
- Compile, full tests, architecture gate, Ruff, Bandit, pip-audit, and coverage gates.
- Coverage gate starts at 70% and must not silently pass below that threshold.

## Security and supply chain
- CodeQL security-extended analysis on pushes, pull requests, and weekly schedule.
- Dependency review blocks newly introduced high-severity vulnerable dependencies.
- Dependabot monitors pip and GitHub Actions dependencies weekly.
- Release workflow generates SBOM, SHA-256 checksum, security-gate evidence, and artifact provenance attestation.
- Minimal explicit GitHub Actions token permissions are used per workflow.

## Cumulative compatibility
- v3.71 and v3.72 developer, graph, stash, and conflict-preview functionality retained.
- v3.73-v3.75 architecture improvements retained.
- v3.76 zero-bare and zero-direct-broad exception gates retained.
