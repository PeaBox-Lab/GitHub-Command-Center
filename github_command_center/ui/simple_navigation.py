from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class MenuItem:
    label:str
    destination:str
    hint:str

@dataclass(frozen=True,slots=True)
class MenuGroup:
    name:str
    description:str
    primary:MenuItem
    secondary:tuple[MenuItem,...]

SIMPLE_MENU=(
 MenuGroup('Changes','Edit, review, stage and commit your current work',MenuItem('Review & commit','Changes Center V2','See changed files, stage them and commit'),(MenuItem('Visual diff','Visual Diff Center','Compare changes side by side'),MenuItem('Stash work','Selective Stash','Temporarily save selected changes'))),
 MenuGroup('History','Understand what changed and when',MenuItem('Browse history','History Center V2','Search commits and inspect patches'),(MenuItem('Who changed this?','Blame Explorer','Trace lines to commits'),MenuItem('Search history','Advanced History Search','Find commits by content or message'))),
 MenuGroup('Branches','Switch, compare and integrate lines of work',MenuItem('Manage branches','Branch Dashboard','See branches, upstreams and divergence'),(MenuItem('Rebase commits','Interactive Rebase','Reorder, squash or edit commits'),MenuItem('Manage worktrees','Worktree Safety','Work safely across linked worktrees'))),
 MenuGroup('Sync','Move changes between local and remote repositories',MenuItem('Pull & push','Push & Pull Center','Safely pull or push the current branch'),(MenuItem('Fetch updates','Fetch Preview','Preview before fetching'),MenuItem('Clean remote refs','Remote Prune Audit','Preview and remove stale tracking refs'))),
 MenuGroup('Review','Check quality before sharing',MenuItem('Run preflight checks','Review Center V2','Review changes and run quality checks'),(MenuItem('Resolve conflicts','Conflict Resolver','Inspect and resolve merge conflicts'),MenuItem('Release readiness','Public Release Readiness','Check required release gates'))),
 MenuGroup('GitHub','Work with pull requests, workflows and security',MenuItem('GitHub overview','GitHub Network Center','View PRs, issues, runs, releases and alerts'),(MenuItem('Run GitHub workflows','GitHub Workflow Center','PR checks, merge, workflow and issue actions'),MenuItem('Plugin safety','Plugin Security Center','Audit extension permissions and trust'))),
 MenuGroup('Release','Prepare and publish a verified release',MenuItem('Publish release','Release Publish Center V2','Tag and publish a GitHub release'),(MenuItem('Release evidence','Release Evidence','Capture release evidence and integrity checks'),MenuItem('Verify update','Verified Update Center','Validate update metadata and installer hash'))),
 MenuGroup('Recover','Restore commits or repository state safely',MenuItem('Recover from reflog','Reflog Recovery','Create a safe recovery branch'),(MenuItem('Find lost commits','Lost & Found Center','Inspect unreachable objects'),MenuItem('Fix detached HEAD','Detached HEAD Recovery','Preserve work from detached HEAD'))),
 MenuGroup('Advanced','Specialized administration and diagnostics',MenuItem('Repository tools','Async Git Operations','Maintenance, integrity and long-running operations'),(MenuItem('Git settings','Git Configuration','Inspect repository and global config'),MenuItem('Repository format','Repository Format Inspector','Inspect repository format and extensions'))),
)

def primary_menu_names():return tuple(g.name for g in SIMPLE_MENU)
def destinations():return tuple(i.destination for g in SIMPLE_MENU for i in (g.primary,*g.secondary))
def find_destination(label):
    for group in SIMPLE_MENU:
        for item in (group.primary,*group.secondary):
            if label in (item.label,item.destination):return group.name
    return 'Advanced'
