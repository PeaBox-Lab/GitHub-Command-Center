# Architecture

## v3.42 architecture baseline

```text
github_command_center/
├── centers/      # staged home for independent feature windows
├── models/       # typed command and repository state models
├── services/     # Git execution, background jobs, preferences
├── ui/           # shared styles and reusable widgets
└── local_git_gui.py  # compatibility module during migration
```

## Engineering rules

1. New Git commands use `GitService`, never `shell=True`.
2. Long operations migrate to `JobService` and do not block Tk's main thread.
3. New feature windows belong under `centers/`.
4. Shared UI belongs under `ui/`.
5. Parser/state logic belongs under `models/` or `services/` and requires tests.
6. The compatibility `git()` wrapper remains temporarily while existing centers migrate incrementally.
