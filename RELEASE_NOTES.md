# GitHub Command Center 3.80.0 Release Notes

Architecture-boundary completion release.

## Improvements
- All 18 feature domains now use the centralized process gateway instead of invoking `subprocess.run` or `subprocess.Popen` directly.
- The strict post-refactor architecture gate is now enforced with zero direct domain process calls.
- Existing Git/GitHub workflows, UI behavior, error handling, CI/security gates, deterministic packaging, manifests, and release-readiness controls remain intact.

## Cumulative compatibility
All v3.71-v3.79 functionality is retained.

## Historical compatibility
v3.72 commit graph filters and stash diff/conflict previews remain retained, together with every subsequent cumulative release improvement.
