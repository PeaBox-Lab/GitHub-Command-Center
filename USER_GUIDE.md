# GitHub Command Center 3.0 User Guide

## Daily workflow
Use Operations Dashboard first. Follow its recommendation, then use Review before committing, Smart Sync before pulling/pushing, and Release Policy before Release Center.

## Plugin Manager
Plugins are local JSON files containing a name, description, command array and enabled flag. Inspect every command before running it. The app does not use shell interpolation, but plugins can still execute local programs with your user permissions.

## Batch Operations
Scan the parent workspace, select repositories and choose an operation. Pull FF-only skips changed repositories. Review each result in the final column.

## Data Export
Use JSON for broad repository metadata and CSV for commit-level analysis in Excel, Power BI, Python or another analytics tool.

## Existing workflows
All earlier centers remain available through Commands, including conflicts, graph, releases, PRs, Actions, security, worktrees, recovery, hooks, LFS, signing, changelog generation and metrics.
