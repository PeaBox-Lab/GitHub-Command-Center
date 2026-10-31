# GitHub Command Center v3.49.0

Version 3.49 is the plugin and extensibility security-hardening release.

## Plugin Security Center

- Manifest schema/version validation
- Semantic-version validation
- Argument-array command requirement
- Executable allowlist
- Explicit permission model
- Trusted-publisher store
- Optional local signature-required policy
- SHA-256 package/executable verification
- Canonical payload generation
- HMAC signing/verification for deterministic local/test workflows
- Audit never executes the plugin

## Permission model

```text
repository.read
repository.write
git.read
git.write
network.github
filesystem.read
filesystem.write
process.execute
```

Unknown permissions or non-allowlisted executables block execution eligibility. Unsigned manifests and undeclared hashes warn by default; local policy can require signatures.

## Trust storage

Trusted publishers and signature policy are stored in:

```text
~/.gccc-plugin-trust.json
```

Trust is explicit and local. It is never inferred from a plugin name or download location.

## Important limitation

The v3.49 HMAC option is appropriate for local deterministic verification and automated tests. Public plugin distribution still requires certificate-backed signatures, publisher identity, revocation, and transparency infrastructure in a future release.
