from __future__ import annotations

from .async_domain import ASYNC_CENTERS
from .branches import BRANCH_CENTERS
from .recovery import RECOVERY_CENTERS
from .releases import RELEASE_CENTERS

CENTER_DOMAINS = {
    "async": ASYNC_CENTERS,
    "recovery": RECOVERY_CENTERS,
    "branches": BRANCH_CENTERS,
    "releases": RELEASE_CENTERS,
}


def all_registered_centers() -> tuple[str, ...]:
    return tuple(name for values in CENTER_DOMAINS.values() for name in values)
