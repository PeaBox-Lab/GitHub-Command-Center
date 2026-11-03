"""Compatibility facade for v3.73 feature imports.

Implementations are organized into bounded domain modules in v3.74.
"""
from ..core.command_gateway import GitError, git
from .domains.expert_refs import *
from .domains.expert_query import *
from .domains.expert_history import *
from .domains.expert_storage import *
from .domains.expert_diagnostics import *
from .domains.expert_revision import *
