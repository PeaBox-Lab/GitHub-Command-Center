# GitHub Command Center 3.76.0 Release Notes

Error-handling hardening release.

## Improvements
- Zero bare exception handlers.
- Zero direct broad `except Exception` handlers.
- Expected operational failures use a centralized typed exception boundary covering Git errors, OS and filesystem failures, invalid values, runtime failures, lookup failures, Unicode failures, and import failures.
- Unexpected programming defects now propagate instead of being silently hidden.
- Structured logging helper records operation context and stack traces.
- Control-flow exceptions including `KeyboardInterrupt` and `SystemExit` are not swallowed.

## Compatibility
All cumulative features and prior compatibility routes remain available.

## Cumulative compatibility
- v3.71 developer and productivity tooling retained.
- v3.72 commit graph filters, stash diff previews, and conflict previews retained.
- v3.73 through v3.75 architecture and compatibility work retained.
