from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class CommandResult:
    args: tuple[str, ...]
    cwd: Path
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and not self.timed_out

    @property
    def output(self) -> str:
        value = "\n".join(x for x in (self.stdout.strip(), self.stderr.strip()) if x)
        return value or "Completed successfully."


@dataclass(slots=True)
class RepositoryState:
    root: Path
    branch: str = ""
    upstream: str = ""
    head: str = ""
    changed_paths: list[str] = field(default_factory=list)
    ahead: int | None = None
    behind: int | None = None

    @property
    def clean(self) -> bool:
        return not self.changed_paths

    @property
    def detached(self) -> bool:
        return not self.branch
