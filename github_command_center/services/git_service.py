from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable

from ..models import CommandResult, RepositoryState


class GitCommandError(RuntimeError):
    def __init__(self, result: CommandResult):
        super().__init__(result.output)
        self.result = result


class GitService:
    """Single argument-array execution boundary for local Git operations."""

    def __init__(self, repository: str | Path, timeout: int = 600):
        self.repository = Path(repository).expanduser().resolve()
        self.timeout = timeout

    def execute(
        self,
        *args: str,
        timeout: int | None = None,
        check: bool = True,
        input_text: str | None = None,
    ) -> CommandResult:
        command = ("git", *map(str, args))
        try:
            process = subprocess.run(
                command,
                cwd=self.repository,
                input=input_text,
                text=True,
                capture_output=True,
                timeout=timeout or self.timeout,
                encoding="utf-8",
                errors="replace",
            )
            result = CommandResult(
                args=command,
                cwd=self.repository,
                returncode=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
            )
        except subprocess.TimeoutExpired as exc:
            result = CommandResult(
                args=command,
                cwd=self.repository,
                returncode=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or f"Timed out after {timeout or self.timeout} seconds.",
                timed_out=True,
            )
        if check and not result.ok:
            raise GitCommandError(result)
        return result

    def text(self, *args: str, **kwargs) -> str:
        return self.execute(*args, **kwargs).output

    def lines(self, *args: str, **kwargs) -> list[str]:
        value = self.execute(*args, **kwargs).stdout
        return [line for line in value.splitlines() if line]

    def repository_state(self) -> RepositoryState:
        state = RepositoryState(root=self.repository)
        state.branch = self.execute("branch", "--show-current").stdout.strip()
        state.head = self.execute("rev-parse", "HEAD").stdout.strip()
        state.changed_paths = self.lines("status", "--porcelain=v1")
        upstream = self.execute(
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{u}",
            check=False,
        )
        if upstream.ok:
            state.upstream = upstream.stdout.strip()
            state.ahead = int(self.execute("rev-list", "--count", "@{u}..HEAD").stdout.strip())
            state.behind = int(self.execute("rev-list", "--count", "HEAD..@{u}").stdout.strip())
        return state

    def ensure_clean(self) -> None:
        state = self.repository_state()
        if not state.clean:
            raise RuntimeError("Commit or stash local changes before continuing.")

    def verify_ref(self, ref: str, object_type: str | None = None) -> str:
        expression = f"{ref}^{{{object_type}}}" if object_type else ref
        return self.execute("rev-parse", "--verify", expression).stdout.strip()

    def create_safety_branch(self, name: str, start_point: str = "HEAD") -> str:
        self.execute("branch", name, start_point)
        return name

    def run_many(self, commands: Iterable[Iterable[str]]) -> list[CommandResult]:
        return [self.execute(*tuple(command)) for command in commands]
