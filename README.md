# GitHub Command Center v3.10.0

Version 3.10 continues decimal versioning within major version 3. This release strengthens team governance, repository navigation and preflight quality checks.

## Branch Protection Advisor
- Reads GitHub branch-protection configuration through authenticated GitHub CLI
- Reviews PR-review requirements, stale-review dismissal, status checks, admin enforcement, force-push and deletion settings
- Provides practical recommendations without automatically mutating server policies
- Opens the repository branch-settings page when deeper administration is needed

## Repository Favorites & Groups
- User-level persistent favorites in `~/.gccc-favorites.json`
- Group repositories by product or purpose
- Add current repository or another local repository folder
- Double-click to open directly in Local Git

## Preflight Quality Gates
- Clean-working-tree check
- Git whitespace validation
- Python source compilation
- Git object integrity check
- Configurable gates, overall PASS/FAIL and exportable report

All tools from v0.1 through v3.9 remain included.
