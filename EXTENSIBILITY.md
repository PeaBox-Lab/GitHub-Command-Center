# Extensibility Guide

## Built-in centers
Advanced GUI tools are independent `tk.Toplevel` centers registered in `CommandPalette.commands` with display name, callable and search keywords.

## JSON command plugins
Plugin files live under `.git/gccc-plugins/*.json` and use this schema:

```json
{
  "name": "Run project tests",
  "description": "Local test command",
  "command": ["python", "-m", "pytest", "-q"],
  "enabled": true
}
```

Commands are executed directly as argument arrays with the repository as working directory. Shell strings are not evaluated. Users must still review plugins because they execute with the current user's permissions.

## Engineering rules
1. Confirm destructive actions.
2. Never display stored secrets.
3. Prefer FF-only pull and normal branch deletion.
4. Keep private state under `.git/gccc-*`.
5. Keep shared controls in tracked project files.
6. Capture command output and exit code.
7. Preserve prior features and cumulative documentation.
8. Add new built-in centers to Command Palette with useful keywords.

## v3.1 platform services
New centers demonstrate reusable patterns for threaded subprocess jobs, user-level JSON preferences, standard-library SQLite persistence and built-in smoke testing. Future modular centers should reuse these patterns when the large GUI module is split into a `centers/` package.
