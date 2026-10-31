# GitHub Command Center v3.47.0

Version 3.47 is the Windows packaging release.

## Distribution targets

- `GitHubCommandCenter.exe`: PyInstaller windowed executable
- `GitHubCommandCenter-3.47.0-portable.zip`: portable package
- `GitHubCommandCenterSetup-3.47.0.exe`: Inno Setup installer
- `SHA256SUMS.txt`: SHA-256 integrity manifest

## Build pipeline

`python scripts/build_release.py` runs tests, compiles Python, builds the PyInstaller executable, creates the portable ZIP, and writes checksums.

GitHub Actions workflow `.github/workflows/windows-package.yml` additionally builds the Inno Setup installer on `windows-latest`, refreshes checksums, runs package smoke tests, and uploads all artifacts.

## Installer behavior

- x64-compatible installation
- Program Files default location
- Start-menu shortcut
- Optional desktop shortcut
- Standard Windows uninstall entry
- README/User Guide/Changelog included

## Safety and provenance

The package pipeline runs the existing test suite before producing binaries. Every release artifact is covered by SHA-256. Code-signing infrastructure is intentionally left as the next hardening step because it requires a real publisher certificate and secret-backed CI configuration.
