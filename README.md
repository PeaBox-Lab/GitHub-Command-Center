# GitHub Command Center v3.36.0

Version 3.36 continues decimal progression within major version 3 with Git wire-protocol diagnostics, shared-object storage inspection, and guarded line-ending normalization.

## New in v3.36

### Git Protocol Diagnostics
- Inspect configured protocol version
- List remote refs and symbolic HEAD
- Cached remote details
- Protocol-v2 packet trace for `ls-remote`
- Redact obvious URL userinfo before display
- Read-only remote diagnostics

### Object Alternates Inspector
- Inspect `.git/objects/info/alternates`
- Inspect `GIT_ALTERNATE_OBJECT_DIRECTORIES`
- Show local object statistics
- Export report
- Optional confirmed `git repack -a -d` to copy reachable objects locally and dissociate from shared storage

### EOL Normalization Center
- Inspect `core.autocrlf`, `core.eol`, and `core.safecrlf`
- Review `.gitattributes`
- Check effective text/EOL/encoding attributes
- Preview renormalization
- Stage `git add --renormalize` only from a clean working tree

All v0.1-v3.35 capabilities remain included through Command Palette.
