# GitHub Command Center v3.57.0

Version 3.57 extracts Changes and History, migrates GitHub network/API calls to JobService, and adds a Windows UI regression suite.

## Architecture phase 4
- `centers/changes/changes_center.py`
- `centers/history/history_center.py`
- `centers/github/async_github_center.py`

## Changes Center V2
- status inventory, stage, unstage, discard, commit and diff
- GitService boundary
- responsive table layout

## History Center V2
- all-ref commit log, search, ref decorations and full patch inspection
- GitService boundary
- responsive table layout

## Async GitHub Network Center
- repository details, PRs, issues, Actions runs, releases
- Dependabot, code-scanning and secret-scanning alerts
- all calls use `gh` argument arrays through JobService
- live output and cancellation

## Windows UI regression
A dedicated matrix runs at 1366x768 and 1920x1080 with 100%, 125% and 150% scaling inputs. It checks table widths, multiline-cell spillover and emits `ui-regression.json` evidence.
