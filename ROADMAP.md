# Roadmap after v3.0

## Near term
- Break the large GUI module into a formal `centers/` package
- Add automated unit tests for parsers and policy logic
- Add background job queue and cancellation for long-running commands
- Add persisted window preferences and theme selection

## Medium term
- Optional SQLite local cache for repository portfolio history
- Visual charts for metrics and Actions trends
- Signed plugin manifests and allowlisted executable policies
- Installer packaging with PyInstaller and Windows signing workflow

## Long term
- GitHub App/OAuth device-flow authentication through a local backend
- Cross-provider adapters for GitLab and Azure DevOps
- Team policy bundles and centrally distributed templates
