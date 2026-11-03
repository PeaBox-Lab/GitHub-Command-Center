# GitHub Command Center 3.81.0 Release Notes

Feature release built on the hardened v3.80 baseline.

## New feature: Workspace Profiles
Save frequently used repository contexts by name, including a preferred branch and note. Open a saved profile to launch the repository and switch to the configured branch. Profiles can be exported/imported as JSON for backup or migration.

## Safety
Opening a profile validates that the repository still exists. A branch-switch failure produces a warning while still opening the repository. Profile writes use a temporary file followed by atomic replacement.

## Cumulative compatibility
All v3.71-v3.80 Git/GitHub functionality, architecture boundaries, error handling, CI/security gates, deterministic packaging, manifests, and release-readiness controls remain retained.

## Historical compatibility
v3.72 commit graph filters plus stash diff and conflict previews remain retained, together with every subsequent cumulative release improvement.
