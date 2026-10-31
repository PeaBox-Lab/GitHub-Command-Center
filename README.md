# GitHub Command Center v3.52.0

Version 3.52 focuses on Windows validation, accessibility regressions, and startup performance profiling.

## Windows validation
- Dedicated `windows-latest` GitHub Actions workflow
- Compile + full tests
- Git and Tkinter availability checks
- Core import smoke tests
- JSON evidence artifact

## Accessibility regression tests
- High-contrast palette regression checks
- Immutable preference-model check
- Keyboard-help content checks
- Headless accessibility-model guard
- Accessibility documentation rule checks

## Startup performance
- Cold subprocess import timings for package, GitService, DiffService, and navigation model
- 2.5-second per-import CI budget
- `startup-performance.json` artifact for regression tracking

No existing v3.51 user-facing workflow is removed.
