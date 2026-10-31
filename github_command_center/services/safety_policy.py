from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SafetyAssessment:
    allowed: bool
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def assess_branch_delete(*, current: bool, worktree_active: bool, merged: bool, ahead: int | None) -> SafetyAssessment:
    blockers = []
    if current:
        blockers.append("Branch is currently checked out.")
    if worktree_active:
        blockers.append("Branch is checked out in a worktree.")
    if not merged:
        blockers.append("Branch is not merged into the comparison branch.")
    if ahead not in (None, 0):
        blockers.append(f"Branch has {ahead} commit(s) ahead of its upstream.")
    return SafetyAssessment(not blockers, blockers)


def assess_history_rewrite(*, clean: bool, detached: bool, protected_branch: bool) -> SafetyAssessment:
    blockers = []
    warnings = []
    if not clean:
        blockers.append("Working tree is not clean.")
    if detached:
        blockers.append("HEAD is detached.")
    if protected_branch:
        warnings.append("The selected branch appears protected or shared.")
    return SafetyAssessment(not blockers, blockers, warnings)
