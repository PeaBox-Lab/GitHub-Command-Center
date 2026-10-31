from __future__ import annotations

import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

PLUGIN_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
PERMISSIONS = {
    "repository.read",
    "repository.write",
    "git.read",
    "git.write",
    "network.github",
    "filesystem.read",
    "filesystem.write",
    "process.execute",
}
DEFAULT_EXECUTABLE_ALLOWLIST = {
    "git",
    "gh",
    "python",
    "python3",
    "pytest",
    "ruff",
    "bandit",
    "pip-audit",
}


@dataclass(slots=True)
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    command: tuple[str, ...]
    permissions: tuple[str, ...] = ()
    publisher: str = ""
    description: str = ""
    sha256: str = ""
    signature: str = ""
    manifest_version: int = 1

    @classmethod
    def from_dict(cls, value: dict) -> "PluginManifest":
        command = value.get("command", [])
        permissions = value.get("permissions", [])
        return cls(
            plugin_id=str(value.get("id", "")),
            name=str(value.get("name", "")),
            version=str(value.get("version", "")),
            command=tuple(map(str, command)) if isinstance(command, list) else (),
            permissions=tuple(map(str, permissions)) if isinstance(permissions, list) else (),
            publisher=str(value.get("publisher", "")),
            description=str(value.get("description", "")),
            sha256=str(value.get("sha256", "")),
            signature=str(value.get("signature", "")),
            manifest_version=int(value.get("manifest_version", 1)),
        )

    def canonical_payload(self) -> bytes:
        value = {
            "command": list(self.command),
            "description": self.description,
            "id": self.plugin_id,
            "manifest_version": self.manifest_version,
            "name": self.name,
            "permissions": list(self.permissions),
            "publisher": self.publisher,
            "sha256": self.sha256,
            "version": self.version,
        }
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@dataclass(slots=True)
class PluginAssessment:
    allowed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class PluginSecurityService:
    def __init__(self, executable_allowlist=None):
        self.executable_allowlist = set(executable_allowlist or DEFAULT_EXECUTABLE_ALLOWLIST)

    def load(self, path: str | Path) -> PluginManifest:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Plugin manifest root must be a JSON object.")
        return PluginManifest.from_dict(value)

    def assess(self, manifest: PluginManifest, *, trusted_publishers=(), require_signature=False) -> PluginAssessment:
        errors = []
        warnings = []
        if manifest.manifest_version != 1:
            errors.append("Unsupported manifest version.")
        if not PLUGIN_ID.fullmatch(manifest.plugin_id):
            errors.append("Plugin id must be 3-64 lowercase characters using letters, digits, dot, underscore, or hyphen.")
        if not manifest.name.strip():
            errors.append("Plugin name is required.")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", manifest.version):
            errors.append("Plugin version must use semantic versioning.")
        if not manifest.command:
            errors.append("Plugin command must be a non-empty argument array.")
        elif Path(manifest.command[0]).name.lower() not in {x.lower() for x in self.executable_allowlist}:
            errors.append(f"Executable is not allowlisted: {manifest.command[0]}")
        for item in manifest.permissions:
            if item not in PERMISSIONS:
                errors.append(f"Unknown permission: {item}")
        if "process.execute" not in manifest.permissions:
            errors.append("process.execute permission is required for command plugins.")
        trusted = set(trusted_publishers)
        if manifest.publisher and manifest.publisher not in trusted:
            warnings.append("Publisher is not in the trusted publisher list.")
        if require_signature and not manifest.signature:
            errors.append("A signature is required by policy.")
        elif not manifest.signature:
            warnings.append("Manifest is unsigned.")
        if not manifest.sha256:
            warnings.append("Executable/package SHA-256 is not declared.")
        return PluginAssessment(not errors, errors, warnings)

    @staticmethod
    def digest(path: str | Path) -> str:
        h = hashlib.sha256()
        with Path(path).open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()

    @staticmethod
    def verify_file(path: str | Path, expected_sha256: str) -> bool:
        return hmac.compare_digest(PluginSecurityService.digest(path), expected_sha256.lower())

    @staticmethod
    def sign_hmac(manifest: PluginManifest, secret: bytes) -> str:
        return hmac.new(secret, manifest.canonical_payload(), hashlib.sha256).hexdigest()

    @staticmethod
    def verify_hmac(manifest: PluginManifest, secret: bytes) -> bool:
        if not manifest.signature:
            return False
        expected = PluginSecurityService.sign_hmac(manifest, secret)
        return hmac.compare_digest(expected, manifest.signature.lower())
