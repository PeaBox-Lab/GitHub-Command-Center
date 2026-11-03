"""Compatibility command gateway.

All UI modules use this boundary rather than invoking Git directly.
"""
from ..services import GitService


class GitError(RuntimeError):
    """User-facing Git operation failure."""


def git(cwd, *args):
    """Run Git through GitService while preserving the established text API."""
    try:
        return GitService(cwd).text(*map(str, args), timeout=900)
    except FileNotFoundError as exc:
        raise GitError("Git is not installed or not on PATH.") from exc
    except Exception as exc:
        raise GitError(str(exc)) from exc
