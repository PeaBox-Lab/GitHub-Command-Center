# GitHub Command Center v3.53.0

Version 3.53 rebuilds the table/message layout correction after review of a real UI sample.

## Corrected globally

The screenshot showed a status value such as `Completed successfully.` being rendered as if it were separate table values, visually appearing as `Co` in the State column and `pleted successfully.` in the File column. v3.53 fixes the shared rendering layer rather than patching only Pre-Commit Review.

### Treeview safeguards
- all inserted cell values are normalized to one visual line
- CR/LF and tab content cannot create accidental multiline table rows
- column headings and cell values expand column widths when needed
- widths are capped at 560 px to keep large messages usable
- horizontal scrolling is attached when total columns outgrow the visible table
- table row height increases to 32 px
- the fix applies before existing screen classes create their Treeviews

### Message-label safeguards
- reusable wrapping helper keeps long status/help messages within their own label area
- wrapping tracks the available label width

The fix applies to Pre-Commit Review and the many history, branch, release, audit, security, repository and advanced-tool tables that reuse ttk.Treeview.
