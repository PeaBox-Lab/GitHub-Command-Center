"""Compatibility facade for v3.73 feature imports.

Implementations are organized into bounded domain modules in v3.74.
"""
from ..core.command_gateway import GitError, git
from .domains.workspace_graph import *
from .domains.workspace_repository import *
from .domains.workspace_productivity import *
from .domains.workspace_automation import *
from .domains.workspace_operations import *
from .domains.workspace_staging import *
