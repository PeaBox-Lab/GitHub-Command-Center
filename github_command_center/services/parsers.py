from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PorcelainEntry:
    x: str
    y: str
    path: str
    original_path: str = ""


def parse_status_porcelain_v1(text: str) -> list[PorcelainEntry]:
    rows: list[PorcelainEntry] = []
    for line in text.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        original = ""
        if " -> " in path:
            original, path = path.split(" -> ", 1)
        rows.append(PorcelainEntry(line[0], line[1], path, original))
    return rows


def parse_nul_paths(data: bytes) -> list[str]:
    return [part.decode("utf-8", errors="replace") for part in data.split(b"\0") if part]


def parse_for_each_ref(text: str) -> list[tuple[str, str, str]]:
    rows = []
    for line in text.splitlines():
        fields = line.split("\t", 2)
        if len(fields) == 3:
            rows.append(tuple(fields))
    return rows
