# GitHub Command Center 3.74.0 Release Notes

Architecture-first upgrade from v3.73. All cumulative functionality and familiar workflows are retained.

## Architecture improvements
- Replaced three 1,500 to 1,750-line feature collections with 18 bounded domain modules.
- Retained small compatibility facades for existing imports and extensions.
- Kept the focused application shell and shared Git command gateway introduced in v3.73.
- Added strict limits for shell size, domain size, classes per domain, and prohibited shell execution.

## Usability and compatibility
- No feature reset and no disruptive UI redesign.
- Daily actions, repository health, grouped navigation, Ctrl+K command palette, graph filters, stash previews, worktrees, recovery, release, GitHub and developer tools remain available.
- Existing class names and compatibility aliases remain valid.

## Validation
- Full Python compilation validation.
- Cumulative automated test suite plus v3.74 architecture tests.
- Deterministic architecture gate and audit evidence included.

## Upgrade
Replace the v3.73 application directory with v3.74. User repositories and Git configuration are not modified by the upgrade.

## Cumulative release history
- v3.71 introduced incremental developer and productivity tooling.
- v3.72 added commit graph filters plus stash diff and conflict previews.
- v3.73 separated the application shell, command gateway, and feature collections.
- v3.74 decomposes those collections into bounded Git-domain modules.
