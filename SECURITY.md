# Security Policy

## Supported release line

The actively maintained line is major version 3. Security fixes should be applied to the newest 3.x release unless a backport is explicitly announced.

## Reporting a vulnerability

Do not open a public issue for credentials, code-execution vulnerabilities, secret leakage, unsafe plugin execution, or release-signing problems. Use GitHub private vulnerability reporting when enabled for the repository, or contact the maintainers privately through the repository owner's published security contact.

Include the affected version, reproduction steps, impact, and whether a proof-of-concept modifies data or executes external commands.

## Security design

- Git commands use argument arrays instead of shell interpolation.
- Destructive workflows favor preview, recovery branches, typed confirmation, and reflog/bundle recovery.
- Plugins require explicit permissions and an executable allowlist.
- Release assets use SHA-256 manifests.
- CI runs Bandit and pip-audit in addition to tests and compilation.

## Secrets

If a credential was committed, rotate/revoke it first. Removing it from the latest commit alone is not sufficient because Git history may still contain the value.
