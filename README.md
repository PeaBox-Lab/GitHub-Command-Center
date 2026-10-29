# GitHub Command Center v3.12.0

Version 3.12 continues decimal versioning within major version 3 and adds safer merge planning, protected reset workflows and transparent Git configuration management.

## Merge Preview Center
- Select a local or remote branch
- Compute merge base
- Preview integration with `git merge-tree` without modifying the working tree
- Clean-tree gate and confirmation for actual merge
- Abort an in-progress merge

## Reset & Recovery Planner
- Preview commits and change summary affected by a reset
- Soft, mixed and hard modes
- Mandatory timestamped `gccc-backup/pre-reset-*` recovery branch
- Extra typed confirmation for hard reset
- Direct link to Reflog Recovery

## Git Configuration Center
- Effective config with origin and scope
- Set or unset local/global values
- Explicit warning for global edits
- Copyable configuration report

All v0.1-v3.11 tools remain included through Command Palette.
