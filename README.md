# GitHub Command Center v3.17.0

Version 3.17 continues the major-version-3 decimal release train and focuses on repository onboarding, technical audit evidence, and lifecycle management of the safety branches created by protected workflows.

## New in v3.17

### Repository Onboarding Center
- Audit starter repository controls
- Initialize Git when needed
- Generate missing README, CHANGELOG, SECURITY, CONTRIBUTING, `.gitignore`, and `.gitattributes` starter files
- Never overwrites existing starter files

### Repository Audit Pack
- Exportable Markdown evidence pack
- Working-tree/branch status
- Remotes
- Recent commits and tags
- Git object integrity
- Effective Git configuration origins

### Safety Branch Manager
- Inventory `gccc-backup/*` branches created by protected rebase/reset/sync/cherry-pick workflows
- Date, hash and subject visibility
- Inspect a safety branch
- Conservative normal `git branch -d` cleanup only
- Unmerged safety branches remain protected

All earlier v0.1-v3.16 capabilities remain available through Command Palette.
