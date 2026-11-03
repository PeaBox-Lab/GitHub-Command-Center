"""Read-only health checks for saved workspace profiles."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from ..core.command_gateway import git
from ..core.error_boundary import HANDLED_EXCEPTIONS
from .workspace_profile_service import WorkspaceProfile

@dataclass(frozen=True)
class WorkspaceHealth:
    exists: bool
    is_git_repository: bool
    preferred_branch_exists: bool
    current_branch: str
    status: str

class WorkspaceHealthService:
    def inspect(self, profile: WorkspaceProfile) -> WorkspaceHealth:
        repo=Path(profile.repository)
        if not repo.exists():
            return WorkspaceHealth(False,False,False,"","Missing")
        try:
            git(repo,"rev-parse","--is-inside-work-tree")
            current=git(repo,"branch","--show-current").strip()
            branch_ok=True
            if profile.branch:
                try: git(repo,"show-ref","--verify","--quiet",f"refs/heads/{profile.branch}")
                except HANDLED_EXCEPTIONS: branch_ok=False
            status="Ready" if branch_ok else "Branch missing"
            return WorkspaceHealth(True,True,branch_ok,current,status)
        except HANDLED_EXCEPTIONS:
            return WorkspaceHealth(True,False,False,"","Not a Git repository")
