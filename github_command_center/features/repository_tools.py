"""Compatibility facade."""
from ..core.command_gateway import GitError, git
from .domains.repository_history import *
from .domains.repository_safety import *
from .domains.repository_productivity import *
from .domains.repository_release import *
from .domains.repository_governance import *
from .domains.repository_inspection import *
