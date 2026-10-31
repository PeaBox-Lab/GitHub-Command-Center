from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class NavigationItem:
    label: str
    keywords: str = ""

@dataclass(frozen=True, slots=True)
class NavigationSection:
    name: str
    icon: str
    items: tuple[NavigationItem, ...] = field(default_factory=tuple)

NAVIGATION_SECTIONS=(
    NavigationSection("Home","H",(NavigationItem("Dashboard","home overview status"),NavigationItem("Command Palette","search all tools"),NavigationItem("Repository Doctor","health diagnose"))),
    NavigationSection("Changes","C",(NavigationItem("Changes","status stage commit diff"),NavigationItem("Visual Diff","side by side word hunk"),NavigationItem("Partial Staging","hunk patch stage"),NavigationItem("Stash Manager","stash selective"))),
    NavigationSection("History","T",(NavigationItem("Visual History","graph log"),NavigationItem("History Browser","browse commit tree"),NavigationItem("Blame Explorer","line author"),NavigationItem("Advanced History Search","grep pickaxe regex"))),
    NavigationSection("Branches","B",(NavigationItem("Branch Dashboard","branch upstream ahead behind"),NavigationItem("Interactive Rebase","rebase squash fixup"),NavigationItem("Cherry-Pick Queue","cherry pick"),NavigationItem("Worktrees","worktree"))),
    NavigationSection("Sync","S",(NavigationItem("Pull Strategy Advisor","pull rebase merge"),NavigationItem("Fetch Preview","fetch prune dry run"),NavigationItem("Upstream Health","remote upstream"),NavigationItem("Async Git Operations","background jobs"))),
    NavigationSection("Review","V",(NavigationItem("Preflight Quality Gates","quality checks"),NavigationItem("Conflict Resolver","merge conflict"),NavigationItem("Compare Branches/Tags","compare diff"),NavigationItem("Signature Audit","sign verify"))),
    NavigationSection("GitHub","G",(NavigationItem("Pull Requests","pr review merge"),NavigationItem("GitHub Actions","actions workflow ci"),NavigationItem("Security","dependabot code secret scanning"),NavigationItem("Branch Protection Advisor","protection rules"))),
    NavigationSection("Release","R",(NavigationItem("Release Center","release publish"),NavigationItem("Release Comparison","tag compare"),NavigationItem("Release Evidence","approval evidence"),NavigationItem("Asset Integrity","sha256 checksum"))),
    NavigationSection("Recover","X",(NavigationItem("Reflog Recovery","reflog lost commit"),NavigationItem("Lost & Found","fsck lost"),NavigationItem("Dangling Object Recovery","unreachable object"),NavigationItem("Safety Branch Manager","backup branch"))),
    NavigationSection("Advanced","A",(NavigationItem("All Refs","ref browser"),NavigationItem("Maintenance","gc fsck pack"),NavigationItem("Git Configuration","config"),NavigationItem("Advanced Tools","plumbing expert"))),
)

def section_names():return tuple(section.name for section in NAVIGATION_SECTIONS)
def find_items(query:str):
    q=query.lower().strip();result=[]
    for section in NAVIGATION_SECTIONS:
        for item in section.items:
            if not q or q in (item.label+" "+item.keywords+" "+section.name).lower():result.append((section.name,item.label))
    return result
