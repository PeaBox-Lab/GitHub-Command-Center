# GitHub Command Center v3.42.0

Version 3.42 is the first architecture and quality release after the v3.41 audit. It prioritizes maintainability, testability, and safe execution over adding more Git commands.

## Architecture foundation

```text
github_command_center/
├── centers/
├── models/
├── services/
├── ui/
└── local_git_gui.py
```

### Central GitService
- Argument-array execution only
- Typed results and errors
- Timeout handling
- Repository-state model
- Ref verification, clean-tree checks, and safety-branch helper
- Existing legacy `git()` calls now route through the central service

### Shared services
- `JobService`: background subprocesses, streaming events, cancellation, status, and exit codes
- `PreferencesService`: centralized defaults, invalid-JSON recovery, and atomic save
- `ui/styles.py`: reusable modern ttk styling

## Automated tests

The initial suite covers Git execution, clean/changed repository state, ref verification, command failures, shell-interpolation resistance, preferences, and typed models.

```bash
python -m unittest discover -s tests -v
```

## Compatibility

The legacy GUI remains during staged migration, retaining the complete v0.1-v3.41 user-facing toolset. New features must use the new architecture, and existing centers will move incrementally to avoid a high-risk one-shot rewrite.
