from __future__ import annotations
from dataclasses import dataclass

@dataclass(slots=True)
class UpdateDecision:
    allowed: bool
    reason: str


def parse_version(value: str) -> tuple[int, int, int]:
    value=value.strip().lstrip("v")
    parts=value.split(".")
    if len(parts)!=3 or not all(x.isdigit() for x in parts):
        raise ValueError("Version must be numeric major.minor.patch")
    return tuple(map(int,parts))


def assess_update(current: str, candidate: str, *, allow_major=False) -> UpdateDecision:
    cur=parse_version(current);new=parse_version(candidate)
    if new<=cur:return UpdateDecision(False,"Candidate is not newer than the installed version.")
    if new[0]!=cur[0] and not allow_major:return UpdateDecision(False,"Major-version update requires explicit opt-in.")
    return UpdateDecision(True,"Candidate is newer and permitted by policy.")
