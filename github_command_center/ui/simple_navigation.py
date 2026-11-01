from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class MenuGroup:
    name:str
    description:str
    primary:tuple[str,...]

SIMPLE_MENU=(
 MenuGroup('Changes','Review, stage and commit current work',('Changes Center V2','Visual Diff Center','Selective Stash')),
 MenuGroup('History','Inspect commits and compare changes',('History Center V2','Blame Explorer','Advanced History Search')),
 MenuGroup('Branches','Create, switch and integrate branches',('Branch Dashboard','Interactive Rebase','Worktree Safety')),
 MenuGroup('Sync','Fetch, pull, push and remote maintenance',('Fetch Preview','Push & Pull Center','Remote Prune Audit')),
 MenuGroup('Review','Validate work before sharing',('Review Center V2','Conflict Resolver','Public Release Readiness')),
 MenuGroup('GitHub','Pull requests, workflows and security',('GitHub Network Center','GitHub Workflow Center','Plugin Security Center')),
 MenuGroup('Release','Prepare, verify and publish releases',('Release Evidence','Release Publish Center V2','Verified Update Center')),
 MenuGroup('Recover','Recover commits and repository state',('Reflog Recovery','Lost & Found Center','Detached HEAD Recovery')),
 MenuGroup('Advanced','Specialized Git administration',('Async Git Operations','Git Configuration','Repository Format Inspector')),
)

def primary_menu_names():return tuple(x.name for x in SIMPLE_MENU)
def find_destination(label):
 for group in SIMPLE_MENU:
  if label in group.primary:return group.name
 return 'Advanced'
