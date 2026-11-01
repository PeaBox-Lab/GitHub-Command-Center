from __future__ import annotations
from dataclasses import dataclass

MIN_BUTTON_PX=80
MIN_TABLE_COLUMN_PX=60
MAX_PRIMARY_ACTIONS_PER_GROUP=3
MAX_MENU_GROUPS=9

@dataclass(frozen=True,slots=True)
class UsabilityIssue:
    severity:str
    message:str

def evaluate_navigation(groups):
    issues=[]
    if len(groups)>MAX_MENU_GROUPS:issues.append(UsabilityIssue('error',f'Too many primary groups: {len(groups)}'))
    names=[g.name for g in groups]
    if len(names)!=len(set(names)):issues.append(UsabilityIssue('error','Duplicate primary navigation group'))
    for g in groups:
        count=1+len(g.secondary)
        if count>MAX_PRIMARY_ACTIONS_PER_GROUP:issues.append(UsabilityIssue('error',f'{g.name} exposes {count} primary actions'))
        if not g.description.strip():issues.append(UsabilityIssue('warning',f'{g.name} lacks a description'))
    return issues
