# Plugin security

## Manifest version 1

Required fields:

- `manifest_version`: `1`
- `id`: lowercase reverse-domain-style identifier, 3-64 characters
- `name`
- `version`: semantic version
- `command`: argument array, never shell text
- `permissions`: explicit capabilities

Supported permissions:

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

## Default executable allowlist

```text
git
gh
python
python3
pytest
ruff
bandit
pip-audit
```

Unknown executables or permissions block the plugin. Missing signatures/hashes produce warnings unless local policy requires signatures.

## Trust model

Trusted publishers are stored locally in `~/.gccc-plugin-trust.json`. Trust is always explicit. The v3.49 HMAC function supports deterministic local verification and tests. Public marketplace signing should use certificate-backed signatures, transparency records, and revocation in a later release.
