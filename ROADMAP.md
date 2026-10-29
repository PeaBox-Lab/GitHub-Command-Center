# Roadmap after v3.1

## Next architecture milestone
- Split `local_git_gui.py` into `centers/`, `services/`, `models/` and `ui/`
- Centralize background-job execution and cancellation
- Add automated unit tests for parsers, release policy, semantic-version selection and plugin validation
- Add schema migrations for preferences and SQLite portfolio data

## Product roadmap
- Visual charts for portfolio history, repository metrics and Actions trends
- Saved repository groups and favorites
- Signed plugin manifests and executable allowlists
- PyInstaller Windows packaging, upgrade channel and code-signing workflow
- OAuth device-flow authentication through a local backend
- GitLab and Azure DevOps provider adapters
