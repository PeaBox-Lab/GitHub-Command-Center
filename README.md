# GitHub Command Center v0.1.0

A real Python desktop application for viewing GitHub statistics, managing repositories and issues, and cloning repositories without navigating GitHub pages.

## Features
- Connect using a fine-grained personal access token
- Dashboard for repositories, stars, forks, and open issues
- Search and sort repositories
- View recent public activity and maintenance insights
- Create repositories and issues
- Clone repositories to a configurable local workspace
- Open repositories in the browser when required
- Optional secure token persistence through the operating system keyring
- No Node.js, npm, Electron, or administrator rights required

## Windows
Double-click `run_windows.bat`. It creates a local virtual environment, installs the optional `keyring` dependency, and starts the app.

## Linux
Run `./run_linux.sh`. Tkinter may need your distribution package, commonly `python3-tk`.

## GitHub permissions
Use a fine-grained token and grant only what you need:
- Metadata: read
- Issues: read/write, if creating issues
- Administration: write, only if creating repositories
- Contents: read, for normal repository access

The token is memory-only by default. If **Remember token** is selected, it is stored through Python `keyring`, which uses Windows Credential Manager, macOS Keychain, or a supported Linux secret service.

## Requirements
- Python 3.10+
- Tkinter
- Internet access for GitHub API calls
- Git on PATH for cloning

## Current scope
Local pull/status helpers are included in the code foundation. The first GUI exposes cloning; commit, push, release creation, tag management, Actions, security alerts, and ZIP publishing are recommended for v0.2.0.
