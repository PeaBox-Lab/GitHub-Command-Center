# GitHub Command Center v3.45.0

Version 3.45 introduces the reusable visual-diff foundation planned after the architecture audit.

## Visual Diff Center

- Side-by-side synchronized diff panes
- Original and modified line numbers
- Myers, minimal, patience, and histogram algorithms
- File-level additions/deletions summary
- Hunk browser
- Word-level highlighting within replacement lines
- Working-tree and staged modes
- Stage a selected hunk
- Unstage a selected hunk
- Binary-file detection
- Optional path filter

## Reusable architecture

- `services/diff_service.py`: typed file/hunk/line models, unified-patch parser, word-diff engine, Git diff and patch-apply boundary
- `ui/diff_widgets.py`: reusable synchronized side-by-side renderer
- `centers/visual_diff.py`: task-focused visual diff and hunk staging center

The implementation uses `git apply --cached` for selected hunk staging and reverse cached apply for unstaging. Existing partial-staging workflows remain available.
