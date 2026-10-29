# GitHub Command Center v2.2.0

Extensible Python desktop command center for Git and GitHub. Version 2.2 bundles credential hygiene, release governance and local engineering metrics while retaining every earlier feature.

## New bundled centers
### Credential & Remote Hygiene
- Inspect remotes and configured credential-helper sources without reading stored secrets
- Detect obvious embedded-credential patterns in HTTPS remotes
- Convert a recognized GitHub origin between SSH and HTTPS
- Display GitHub CLI authentication status

### Release Policy Center
- Repository-local release requirements stored under `.git/gccc-release-policy.json`
- Optional gates for clean working tree, upstream, CHANGELOG and SECURITY policy
- Overall PASS/BLOCKED result
- Semantic-version suggestion from latest tag and Conventional Commit history
- Major bump for breaking changes, minor for features, patch otherwise

### Repository Metrics
- Commit and tracked-file counts
- Contributor shortlog
- Heuristic line counts by common source/document languages
- Commit activity by month for the latest 24 active months
- Exportable local report with no external analytics service

## Architecture
All advanced functionality remains independently registered in the searchable Command Palette. Private preferences remain under `.git/gccc-*`; shared project controls remain normal tracked files.

## Requirements
Python 3.10+ and Git. GitHub CLI is required for GitHub-hosted PR, Actions, Release, security and auth-status features. Optional GPG and Git LFS integrations remain supported.
