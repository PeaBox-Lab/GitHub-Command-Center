"""Compatibility facade."""
from ..core.command_gateway import GitError, git
from .domains.expert_refs import *
from .domains.expert_query import *
from .domains.expert_history import *
from .domains.expert_storage import *
from .domains.expert_diagnostics import *
from .domains.expert_revision import *
