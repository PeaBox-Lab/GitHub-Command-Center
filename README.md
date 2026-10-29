# GitHub Command Center v0.7.0

Python desktop command center replacing routine GitHub web and TortoiseGit workflows.

## New Security & Dependency Center
- Consolidated security summary for the selected GitHub repository
- Open Dependabot alerts with severity, package and manifest
- Code-scanning alerts with severity, rule and analysis tool
- Secret-scanning alerts with secret type and location
- Open a selected alert in GitHub for remediation details
- Permission and feature warnings when a security API is unavailable
- Local audit for suspicious tracked filenames, tracked files over 10 MB and `git fsck`
- Optional `pip-audit` dependency scan
- Optional Bandit Python static-security scan
- SHA-256 checksum generation for release assets
- Remediation priority: secrets first, then critical/high dependencies, then code-scanning findings

## Previous capabilities retained
- GitHub dashboard, repositories, issues and statistics
- Full local Git workspace, visual graph and three-pane conflict resolution
- Advanced cherry-pick, rebase, revert, guarded reset and `.gitignore` tools
- Release Center with tags, assets, GitHub releases, bundles and ZIP exports
- Pull Request Center
- GitHub Actions workflow dashboard and controls

## Requirements
Python 3.10+, Git, and authenticated GitHub CLI for GitHub security/PR/Actions/Release features. Optional local scanners: `python -m pip install pip-audit bandit`.
