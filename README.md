# GitHub Command Center v3.27.0

Version 3.27 continues decimal progression within major version 3 and adds protected multi-commit revert workflows, an advanced log-query builder, and index-level inspection.

## New in v3.27

### Revert Queue Center
- Browse up to 300 non-merge commits
- Build an ordered revert queue
- Reorder and remove queue items
- Clean-tree safety gate
- Automatic `gccc-backup/pre-revert-*` branch
- Continue or abort after conflicts
- Creates normal revert commits rather than rewriting history

### Git Log Query Builder
- Author filter
- Since/until date filters
- Commit-message grep
- Optional path filter
- All/only/no merge commits
- Export query results

### Git Index Inspector
- Inspect index mode, object ID, stage and path
- View staged blob content
- Inspect `ls-files -v` flags
- Understand merge conflict stages 1/2/3
- Safely unstage selected paths without discarding working-tree content

All v0.1-v3.26 tools remain included through Command Palette.
