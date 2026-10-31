"""Feature-center package introduced in v3.42.

Existing centers continue to load from local_git_gui during the staged migration.
New or migrated centers should be placed in this package and registered through
Command Palette without growing the legacy monolith.
"""
