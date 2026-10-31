# GitHub Command Center v3.22.0

Version 3.22 continues decimal progression within major version 3 and adds local credential-leak review, ref-consistency diagnostics, and a guarded release-branch workflow.

## New in v3.22

### Credential Redaction Audit
- Scan tracked text files up to 2 MB
- GitHub-token, AWS-key, private-key and generic-secret assignment patterns
- Redacted UI/report output rather than printing the suspected secret
- Exportable audit evidence
- Handoff to Security Center

### Ref Consistency Center
- Inspect HEAD symbolic ref
- Inspect origin default-branch symbolic ref
- Show local refs including dereferenced annotated tags
- Connectivity-only fsck
- Fetch/prune and refresh

### Release Branch Planner
- Choose a deliberate base ref
- Preview base commit/history
- Clean-tree and ref-validation gates
- Create and switch to a named release branch

All prior v0.1-v3.21 features remain included through Command Palette.
