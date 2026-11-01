# GitHub Command Center v3.62.0

Version 3.62 is a debt-reduction and UI-simplification release with no intended feature removal.

## Legacy retirement
Eight more duplicate implementations were removed from `local_git_gui.py`: Submodule, Git LFS, Clone, Bundle Inspector, Release Evidence, Change Review, Maintenance Schedule and Commit Graph Maintenance. Thin compatibility aliases preserve old internal names while routing to the extracted implementations.

## Simpler UI model
The primary navigation contract is reduced to nine user-oriented groups: Changes, History, Branches, Sync, Review, GitHub, Release, Recover and Advanced. Each group exposes no more than three primary destinations; the full Command Palette remains available for specialized tools.

## Guardrails
Architecture CI budgets are lowered again. Functionality is retained by aliasing retired classes to tested extracted centers before deleting implementation bodies.
