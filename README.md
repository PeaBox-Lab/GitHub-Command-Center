# GitHub Command Center v3.60.0

Version 3.60 is the planned stabilization milestone.

## Async completion
- Extracted asynchronous Submodule Center: add, sync, recursive init/update
- Extracted asynchronous Git LFS Center: track, fetch all, pull and guarded prune
- Extracted asynchronous Clone Center: full/shallow/partial clone with cancellation and streamed output

## Verified updater foundation
- Version-policy enforcement
- Update metadata model
- SHA-256 verification of downloaded installers
- Metadata generator for release pipelines
- No silent installation or automatic execution

## Windows signing hooks
- Optional secret-backed Authenticode signing in the Windows package workflow
- SHA-256 timestamping through DigiCert's timestamp endpoint
- PowerShell signature verification gate
- Unsigned builds continue when signing secrets are not configured

## Architecture stabilization
- v3.59 duplicate retirement retained
- CI architecture budgets tightened to the v3.59 baseline
- Direct synchronous `gh` calls remain at zero
- No `shell=True`

## Release policy
Windows UI regression and validation workflows remain separate evidence-producing gates. Production publishing should require their successful completion together with CI, package smoke tests and architecture gates.
