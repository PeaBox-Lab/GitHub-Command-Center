from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .git_service import GitService


@dataclass(slots=True)
class TimingResult:
    name: str
    seconds: float
    ok: bool
    detail: str = ""


class ReliabilityService:
    """Small repeatable reliability/performance probes for real Git repositories."""

    def __init__(self, repository: str | Path):
        self.repository = Path(repository).resolve()
        self.git = GitService(self.repository)

    def time_call(self, name: str, function: Callable[[], object]) -> TimingResult:
        start = time.perf_counter()
        try:
            function()
            return TimingResult(name, time.perf_counter() - start, True)
        except Exception as exc:
            return TimingResult(name, time.perf_counter() - start, False, str(exc))

    def standard_probes(self) -> list[TimingResult]:
        return [
            self.time_call("status", lambda: self.git.execute("status", "--porcelain=v1")),
            self.time_call("recent_log", lambda: self.git.execute("log", "-100", "--oneline")),
            self.time_call("refs", lambda: self.git.execute("for-each-ref", "--format=%(refname)")),
            self.time_call("object_count", lambda: self.git.execute("count-objects", "-vH")),
        ]

    @staticmethod
    def save(path: str | Path, values: list[TimingResult]) -> None:
        Path(path).write_text(json.dumps([asdict(value) for value in values], indent=2), encoding="utf-8")
