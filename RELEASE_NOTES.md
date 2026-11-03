# GitHub Command Center 3.75.0 Release Notes

Architecture-completion release based on v3.74. All cumulative functionality and familiar workflows are retained.

## Architecture completion
- The UI shell remains focused and all feature implementations remain in 18 bounded domains.
- Git execution remains routed through `GitService` via the command gateway.
- External processes and byte-oriented Git helpers now route through one process gateway.
- Direct subprocess execution is prohibited inside feature-domain modules.
- Compatibility facades preserve prior imports and extension behavior.

## Compatibility
- No feature reset or disruptive UI redesign.
- v3.71 developer tooling, v3.72 graph/stash functionality, v3.73 shell split, and v3.74 bounded domains remain cumulative.
- Daily actions, branches, commits, history, stash, worktrees, recovery, release, GitHub, developer and expert tools remain available.

## Validation
- Python compile validation.
- Full cumulative automated suite plus v3.75 architecture tests.
- Architecture audit and strict architecture gate included.
