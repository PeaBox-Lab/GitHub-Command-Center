# Extensibility Guide

Advanced tools are implemented as independent `tk.Toplevel` centers in `github_command_center/local_git_gui.py`. Register a new center in `CommandPalette.commands` using a display name, launch callable and search keywords.

Repository-local private state belongs under `.git/gccc-*` so it does not enter normal commits. Shared project configuration should use normal tracked files such as `.gitattributes`, `.gitignore`, `.github/*` or a future documented project config.

New operations should:
1. Use argument arrays rather than shell interpolation.
2. Confirm destructive actions.
3. Prefer safe defaults such as FF-only pull and non-force branch deletion.
4. Display command output and errors.
5. Preserve prior features and update cumulative documentation.
