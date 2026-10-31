# GitHub Command Center v3.20.0

Version 3.20 continues the decimal major-version-3 release train with automated regression hunting, flexible revision archives, and deeper commit metadata inspection.

## New in v3.20

### Automated Bisect Center
- Known-good and known-bad refs
- Configurable local test command
- `git bisect run` automation
- Clean-working-tree safety gate
- Visible output and explicit bisect reset

### Revision Archive Center
- Export HEAD, a branch, tag, or commit as ZIP
- Optional historical subdirectory export
- Optional top-level archive prefix
- No checkout required

### Commit Metadata Inspector
- Raw commit metadata
- Tree and parent IDs
- Author vs committer identity and dates
- Signature status, signer and key information
- Full commit message
- Copyable metadata report

All v0.1-v3.19 capabilities remain included through Command Palette.
