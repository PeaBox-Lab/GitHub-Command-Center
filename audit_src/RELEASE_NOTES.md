# GitHub Command Center 3.73.0 Release Notes

Architecture-focused upgrade from v3.72. All cumulative functionality is retained.

## Highlights
- Replaced the 5,100-line Local Git monolith with a small application shell plus workspace, repository, and expert feature modules.
- Introduced a shared Git command gateway without changing established Git behavior or user workflows.
- Preserved extension-facing imports and all compatibility aliases.
- Retained the existing user-friendly workspace, daily actions, grouped navigation, keyboard command palette, accessibility, graph filters, stash previews, worktrees, recovery, release, developer, and GitHub tools.

## Validation
- Python compile validation passed.
- 208 cumulative automated tests passed.
- Architecture gate passed with the shell below 300 lines and one top-level shell class.

## Upgrade
Replace the v3.72 application directory with v3.73. User repositories and Git configuration are not modified by the upgrade.

## Cumulative compatibility
This release retains the complete v3.71 and v3.72 feature sets, including developer tooling, commit graph filters, stash previews, worktree management, recovery, release, and GitHub workflows.
