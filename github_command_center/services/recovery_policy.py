from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RecoveryDecision:
    method: str
    destructive: bool
    rationale: str


def choose_recovery(*, reflog_available: bool, commit_known: bool, fsck_candidate: bool) -> RecoveryDecision:
    if reflog_available:
        return RecoveryDecision("reflog_branch", False, "Create a recovery branch from the reflog entry before resetting existing refs.")
    if commit_known:
        return RecoveryDecision("direct_branch", False, "Preserve the known commit with a new branch.")
    if fsck_candidate:
        return RecoveryDecision("fsck_branch", False, "Inspect an unreachable commit and preserve it with a branch.")
    return RecoveryDecision("bundle_or_backup", False, "No local ref/object candidate is known; inspect verified backups or bundles.")
