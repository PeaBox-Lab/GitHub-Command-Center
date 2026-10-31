# GitHub Command Center v3.43.0

Version 3.43 continues the architecture repair with CI, expanded tests, parser/safety modules, and domain-based center registries.

## GitHub Actions CI

`.github/workflows/ci.yml` runs on Windows and Ubuntu with Python 3.10 and 3.12:

- `compileall`
- standard-library unit tests
- Ruff critical lint rules
- Bandit security scan
- pip-audit dependency scan

A separate release-smoke workflow runs on `v3.*` tags and supports manual execution.

## Expanded tests

The suite now covers:

- Git execution and repository state
- Preferences and typed models
- Background job completion/cancellation behavior
- Porcelain status and ref parsing
- NUL-separated paths
- Branch-delete safety policy
- History-rewrite safety policy
- Center-domain registry integrity
- Git service clean-tree/safety-branch helpers

## Modular migration

Added explicit domain registries:

```text
centers/
├── recovery.py
├── branches.py
├── releases.py
└── registry.py
```

The existing class implementations remain compatible while migration continues incrementally.
