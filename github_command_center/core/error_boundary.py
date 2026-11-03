"""Typed, observable error boundary for user-initiated operations."""
from __future__ import annotations
import logging
from .command_gateway import GitError
HANDLED_EXCEPTIONS=(GitError,OSError,ValueError,RuntimeError,TypeError,LookupError,UnicodeError,ImportError)
log=logging.getLogger("github_command_center")
def report_error(context,exc):
 log.exception("%s failed: %s",context,exc)
 return f"{context} failed: {exc}"
