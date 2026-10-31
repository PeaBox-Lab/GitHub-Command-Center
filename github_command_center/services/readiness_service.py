from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .git_service import GitService


@dataclass(slots=True)
class ReadinessCheck:
    name: str
    status: str
    detail: str
    required: bool = True


@dataclass(slots=True)
class ReadinessReport:
    repository: str
    checks: list[ReadinessCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.status == "PASS" for c in self.checks if c.required)

    @property
    def score(self) -> int:
        if not self.checks:
            return 0
        passed = sum(c.status == "PASS" for c in self.checks)
        return round(passed / len(self.checks) * 100)

    def to_json(self) -> str:
        return json.dumps({"repository": self.repository, "passed": self.passed, "score": self.score, "checks": [asdict(c) for c in self.checks]}, indent=2)


class ReadinessService:
    """Public-release readiness checks that do not mutate repository state."""

    REQUIRED_FILES = ("README.md", "CHANGELOG.md", "RELEASE_NOTES.md", "USER_GUIDE.md", "SECURITY.md")

    def __init__(self, repository: str | Path):
        self.repository = Path(repository).resolve()
        self.git = GitService(self.repository)

    def assess(self) -> ReadinessReport:
        report = ReadinessReport(self.repository.name)
        state = self.git.repository_state()
        report.checks.append(ReadinessCheck("Working tree", "PASS" if state.clean else "FAIL", "Clean" if state.clean else f"{len(state.changed_paths)} changed path(s)"))
        report.checks.append(ReadinessCheck("Attached branch", "PASS" if not state.detached else "FAIL", state.branch or "Detached HEAD"))
        report.checks.append(ReadinessCheck("Git integrity", "PASS" if self.git.execute("fsck", "--no-progress", check=False).ok else "FAIL", "git fsck --no-progress"))
        for name in self.REQUIRED_FILES:
            exists = (self.repository / name).exists()
            report.checks.append(ReadinessCheck(name, "PASS" if exists else "FAIL", "Present" if exists else "Missing"))
        tests = self.repository / "tests"
        test_count = len(list(tests.glob("test_*.py"))) if tests.exists() else 0
        report.checks.append(ReadinessCheck("Automated tests", "PASS" if test_count >= 10 else "WARN", f"{test_count} test module(s)", required=False))
        ci = self.repository / ".github" / "workflows" / "ci.yml"
        report.checks.append(ReadinessCheck("CI workflow", "PASS" if ci.exists() else "FAIL", "Present" if ci.exists() else "Missing"))
        packaging = self.repository / ".github" / "workflows" / "windows-package.yml"
        report.checks.append(ReadinessCheck("Windows package workflow", "PASS" if packaging.exists() else "WARN", "Present" if packaging.exists() else "Missing", required=False))
        return report
