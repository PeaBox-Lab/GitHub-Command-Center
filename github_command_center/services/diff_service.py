from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path

from .git_service import GitService


@dataclass(slots=True)
class DiffLine:
    kind: str
    old_number: int | None
    new_number: int | None
    text: str
    words: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class DiffHunk:
    header: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[DiffLine] = field(default_factory=list)


@dataclass(slots=True)
class FileDiff:
    path: str
    old_path: str = ""
    status: str = "M"
    binary: bool = False
    hunks: list[DiffHunk] = field(default_factory=list)

    @property
    def additions(self) -> int:
        return sum(1 for hunk in self.hunks for line in hunk.lines if line.kind == "add")

    @property
    def deletions(self) -> int:
        return sum(1 for hunk in self.hunks for line in hunk.lines if line.kind == "delete")


class DiffParser:
    """Parse unified Git patches into typed file/hunk/line models."""

    @staticmethod
    def parse(patch: str) -> list[FileDiff]:
        import re

        files: list[FileDiff] = []
        current: FileDiff | None = None
        hunk: DiffHunk | None = None
        old_no = new_no = 0
        header_re = re.compile(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)")
        for raw in patch.splitlines():
            if raw.startswith("diff --git "):
                parts = raw.split(" ", 3)
                old_path = parts[2][2:] if len(parts) > 2 else ""
                path = parts[3][2:] if len(parts) > 3 else old_path
                current = FileDiff(path=path, old_path=old_path)
                files.append(current)
                hunk = None
                continue
            if current is None:
                continue
            if raw.startswith("new file mode"):
                current.status = "A"
            elif raw.startswith("deleted file mode"):
                current.status = "D"
            elif raw.startswith("rename from "):
                current.status = "R"
                current.old_path = raw[12:]
            elif raw.startswith("rename to "):
                current.path = raw[10:]
            elif raw.startswith("Binary files ") or raw.startswith("GIT binary patch"):
                current.binary = True
            elif raw.startswith("@@"):
                match = header_re.match(raw)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2) or 1)
                    new_start = int(match.group(3))
                    new_count = int(match.group(4) or 1)
                    old_no, new_no = old_start, new_start
                    hunk = DiffHunk(raw, old_start, old_count, new_start, new_count)
                    current.hunks.append(hunk)
            elif hunk is not None:
                if raw.startswith("+") and not raw.startswith("+++"):
                    hunk.lines.append(DiffLine("add", None, new_no, raw[1:]))
                    new_no += 1
                elif raw.startswith("-") and not raw.startswith("---"):
                    hunk.lines.append(DiffLine("delete", old_no, None, raw[1:]))
                    old_no += 1
                elif raw.startswith(" "):
                    hunk.lines.append(DiffLine("context", old_no, new_no, raw[1:]))
                    old_no += 1
                    new_no += 1
                elif raw.startswith("\\ No newline"):
                    hunk.lines.append(DiffLine("meta", None, None, raw))
        DiffParser._annotate_words(files)
        return files

    @staticmethod
    def _annotate_words(files: list[FileDiff]) -> None:
        for file_diff in files:
            for hunk in file_diff.hunks:
                lines = hunk.lines
                index = 0
                while index < len(lines):
                    deleted: list[DiffLine] = []
                    added: list[DiffLine] = []
                    while index < len(lines) and lines[index].kind == "delete":
                        deleted.append(lines[index]); index += 1
                    while index < len(lines) and lines[index].kind == "add":
                        added.append(lines[index]); index += 1
                    for left, right in zip(deleted, added):
                        left.words, right.words = word_diff(left.text, right.text)
                    if not deleted and not added:
                        index += 1


def word_diff(old: str, new: str) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """Return token segments tagged equal/delete/add for inline highlighting."""
    import re

    tokenize = lambda value: re.findall(r"\s+|[A-Za-z0-9_]+|[^\w\s]", value)
    a, b = tokenize(old), tokenize(new)
    matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    left: list[tuple[str, str]] = []
    right: list[tuple[str, str]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            left.append(("equal", "".join(a[i1:i2])))
            right.append(("equal", "".join(b[j1:j2])))
        elif tag == "delete":
            left.append(("delete", "".join(a[i1:i2])))
        elif tag == "insert":
            right.append(("add", "".join(b[j1:j2])))
        else:
            left.append(("delete", "".join(a[i1:i2])))
            right.append(("add", "".join(b[j1:j2])))
    return left, right


class DiffService:
    """Git-backed diff operations and patch staging boundary."""

    def __init__(self, repository: str | Path):
        self.git = GitService(repository)
        self.repository = Path(repository).resolve()

    def patch(self, *, staged: bool = False, left: str = "", right: str = "", path: str = "", algorithm: str = "histogram") -> str:
        args = ["diff", "--no-ext-diff", "--no-color", f"--diff-algorithm={algorithm}", "--find-renames"]
        if staged:
            args.append("--cached")
        if left and right:
            args += [left, right]
        elif left:
            args.append(left)
        if path:
            args += ["--", path]
        return self.git.execute(*args).stdout

    def files(self, **kwargs) -> list[FileDiff]:
        return DiffParser.parse(self.patch(**kwargs))

    def apply_patch(self, patch: str, *, cached: bool = True, reverse: bool = False) -> str:
        args = ["apply", "--whitespace=nowarn"]
        if cached:
            args.append("--cached")
        if reverse:
            args.append("--reverse")
        args.append("-")
        return self.git.execute(*args, input_text=patch).output

    @staticmethod
    def hunk_patch(file_diff: FileDiff, hunk: DiffHunk) -> str:
        old_path = file_diff.old_path or file_diff.path
        return "\n".join([
            f"diff --git a/{old_path} b/{file_diff.path}",
            f"--- a/{old_path}",
            f"+++ b/{file_diff.path}",
            hunk.header,
            *[("+" if line.kind == "add" else "-" if line.kind == "delete" else " " if line.kind == "context" else "") + line.text for line in hunk.lines],
            "",
        ])
