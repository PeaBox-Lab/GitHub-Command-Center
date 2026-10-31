# GitHub Command Center v3.46.0

Version 3.46 is the task-based navigation redesign release. It reduces feature-discovery friction without removing the Command Palette or any existing Git/GitHub capability.

## New navigation model

The product taxonomy is now organized around developer outcomes:

1. **Home** – dashboard, Command Palette, Repository Doctor
2. **Changes** – working tree, Visual Diff, partial staging, stash
3. **History** – graph, historical browser, blame, history search
4. **Branches** – branch dashboard, interactive rebase, cherry-pick, worktrees
5. **Sync** – pull strategy, fetch preview, upstream health, async operations
6. **Review** – preflight, conflicts, comparisons, signature audit
7. **GitHub** – pull requests, Actions, security, branch protection
8. **Release** – release publishing, comparisons, evidence, checksums
9. **Recover** – reflog, lost-found, dangling objects, safety branches
10. **Advanced** – refs, maintenance, config and plumbing tools

`Ctrl+K` remains the complete power-user discovery surface.

## Navigation service

`ui/navigation.py` provides typed task sections, labels, keywords, and search. This gives future workspaces a single navigation source instead of duplicating category definitions inside Tk windows.

## Compatibility

No major Git workflow has been removed. Existing center classes and the complete Command Palette remain available while the main navigation progressively adopts the task taxonomy.
