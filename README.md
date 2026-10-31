# GitHub Command Center v3.50.0

Version 3.50 is the public-release hardening milestone for the major-version-3 line.

## Public Release Readiness

A new readiness center evaluates:

- clean working tree
- attached branch
- Git object integrity
- README, CHANGELOG, RELEASE_NOTES, USER_GUIDE, SECURITY policy
- automated-test presence
- CI workflow
- Windows package workflow

It produces a readiness score, required-gate PASS/FAIL result, and exportable JSON evidence.

## Update policy

A small update-policy service now enforces numeric `major.minor.patch` comparisons and blocks major-version jumps unless explicitly opted in. This matches the project's policy of continuing incremental work within major version 3.

## Security and contribution baseline

Added repository-grade `SECURITY.md` and `CONTRIBUTING.md` covering private vulnerability reporting, command-execution safety, secret rotation, tests, destructive-operation controls, and documentation requirements.

## Test milestone

v3.50 expands automated coverage across release readiness, update policy, plugin-manifest edge cases, recovery, rebase, conflicts, packaging, diffs, jobs, parsers, and Git services.
