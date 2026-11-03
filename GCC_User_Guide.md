**Document status: source-based draft; actual screenshots pending.**

This guide explains how to use GCC in everyday language. It is based on the supplied v3.53.0 source-code collection and its bundled documentation. The application has not been run or tested during preparation of this guide. Where a screen has not been inspected directly, use the exact Command Palette entry given here rather than relying on a sidebar location.

**About screenshots:** no screenshots were included in the supplied attachment. Each numbered workflow step below includes a “Capture” note describing the real screen to photograph. These notes are not screenshots. Replace them with actual captures from your running application before distributing this as an illustrated final guide. Never show access tokens, passwords, private keys, or confidential repository data.

**Version note:** the supplied package identifies itself as v3.53.0, but some window titles and older guide headings still say 3.2 or another earlier version. The code also defines a newer task-based navigation model alongside the older workspace sidebar. Confirm which navigation your running build shows. Ctrl+K is the most consistent route to the full toolset.

**How to read this guide:** start with Getting Started and Your First Working Day. Use the feature reference when you need a less common tool. Read the warning before any action that deletes files, changes history, publishes content, or runs commands.

# Contents

[Contents [1](#contents)](#contents)

[1. Understand GCC before you start [1](#understand-gcc-before-you-start)](#understand-gcc-before-you-start)

[1.1 The words you will see every day [2](#the-words-you-will-see-every-day)](#the-words-you-will-see-every-day)

[1.2 Safety rules worth keeping [2](#safety-rules-worth-keeping)](#safety-rules-worth-keeping)

[2. Getting Started [3](#getting-started)](#getting-started)

[2.1 What you need [3](#what-you-need)](#what-you-need)

[2.2 Start the application [3](#start-the-application)](#start-the-application)

[2.3 Connect your GitHub account [4](#connect-your-github-account)](#connect-your-github-account)

[2.4 Set your local workspace [4](#set-your-local-workspace)](#set-your-local-workspace)

[2.5 Clone an existing project [4](#clone-an-existing-project)](#clone-an-existing-project)

[2.6 Confirm readiness [5](#confirm-readiness)](#confirm-readiness)

[2.7 Disconnect safely [5](#disconnect-safely)](#disconnect-safely)

[3. Find your way around [5](#find-your-way-around)](#find-your-way-around)

[3.1 Main account window [5](#main-account-window)](#main-account-window)

[3.2 Local Git Workspace [6](#local-git-workspace)](#local-git-workspace)

[3.3 Command Palette: your route to every feature [6](#command-palette-your-route-to-every-feature)](#command-palette-your-route-to-every-feature)

[3.4 Task groups and older sidebar labels [6](#task-groups-and-older-sidebar-labels)](#task-groups-and-older-sidebar-labels)

[3.5 Reading wide tables in v3.53 [7](#reading-wide-tables-in-v3.53)](#reading-wide-tables-in-v3.53)

[4. Your First Working Day [7](#your-first-working-day)](#your-first-working-day)

[4.1 Start from a known state [7](#start-from-a-known-state)](#start-from-a-known-state)

[4.2 Create a branch and edit files [7](#create-a-branch-and-edit-files)](#create-a-branch-and-edit-files)

[4.3 Review, stage, and commit [7](#review-stage-and-commit)](#review-stage-and-commit)

[4.4 Publish your branch [8](#publish-your-branch)](#publish-your-branch)

[5. Manage Changes Without Losing Work [8](#manage-changes-without-losing-work)](#manage-changes-without-losing-work)

[5.1 Stage only part of a file [8](#stage-only-part-of-a-file)](#stage-only-part-of-a-file)

[5.2 Put unfinished work aside with a stash [8](#put-unfinished-work-aside-with-a-stash)](#put-unfinished-work-aside-with-a-stash)

[5.3 Merge a branch into your current branch [8](#merge-a-branch-into-your-current-branch)](#merge-a-branch-into-your-current-branch)

[5.4 Resolve a conflict [8](#resolve-a-conflict)](#resolve-a-conflict)

# 1. Understand GCC before you start

GCC brings Git work on your computer and GitHub work online into one desktop application. The main account window helps you browse repositories, create issues, and see activity. The Local Git Workspace handles files, commits, branches, synchronization, and a large collection of specialist tools.

## 1.1 The words you will see every day

| **Word** | **Everyday meaning** |
|----|----|
| Repository / repo | A project folder plus Git’s record of its history. A GitHub repository is the online copy. |
| Working tree | The files you are currently editing on your computer. |
| Stage / index | Choose the exact changes to include in your next commit. Staging is not publishing. |
| Commit | A recorded snapshot of staged changes with a message explaining what changed. |
| Branch | A named line of work. It lets you develop a change separately from other work. |
| HEAD / detached HEAD | Your current position in history. Detached HEAD means you are viewing a commit without being on a normal branch. |
| Remote / origin | A saved address for another copy of the repository. “origin” is the usual name of the first remote. |
| Upstream | The remote branch your local branch tracks for pull and push comparisons. |
| Fetch / pull / push | Fetch downloads remote history. Pull brings remote changes into your current branch. Push sends your local commits to the remote. |
| Diff / hunk | A diff shows what changed. A hunk is one nearby block of changed lines. |
| Stash | A temporary place to put unfinished work so you can switch tasks. |
| Tag / release | A tag names a point in history. A GitHub release adds publication notes and downloadable assets around a tag. |
| Ref / SHA / object ID | A ref is a name pointing into Git history. An object ID identifies a stored commit, file, tree, or tag. |
| Rebase / revert / reset | Rebase rewrites commits onto another base. Revert adds a new commit that undoes a change. Reset moves your current branch and may also change staged or working files. |
| Worktree / submodule / subtree | A worktree is another checkout of the same repository. A submodule is a linked repository inside a parent project. A subtree copies another project’s content into your project. |

## 1.2 Safety rules worth keeping

- Check the repository path and current branch before changing anything.

- Commit or stash unfinished work before switching context, rebasing, resetting, or changing sparse checkout.

- A recovery branch protects committed history, not unsaved or uncommitted files. Keep a separate backup of important unfinished work.

- Preview before cleaning, pruning, deleting, merging, or changing remote mappings.

- Use ordinary Push for normal work. Force-with-Lease is a specialist action after an intentional history rewrite.

- Read exported reports before sharing. Configuration, remote addresses, logs, source archives, and bundles may contain sensitive information.

- Do not run plugins, hooks, recipes, or test commands from sources you do not trust.

# 2. Getting Started

## 2.1 What you need

For source launch, use Python 3.10 or later with a working Tk desktop environment, plus Git available to the application. The supplied Windows and Linux launchers create a local virtual environment and install the listed dependency, keyring. They may need internet access and permission to write in the application folder. The attachment is a text collection of files, not an installable executable or an extracted application folder.

Some GitHub features use the GitHub CLI, named gh. Install and authenticate it separately before using Pull Request Center, GitHub Actions Center, Release Center, and GitHub security checks. Logging into the main account window with a personal access token does not automatically log gh in. Git network access also uses Git’s own HTTPS credential helper or SSH setup; it is separate from the main window’s token.

Git LFS, signing tools, external diff/merge tools, pip-audit, and Bandit are additional requirements only for the features that use them. Availability depends on your installed tools, permissions, and repository setup.

## 2.2 Start the application

1.  **Obtain the actual GCC v3.53.0 distribution.** Use a trusted source and check the supplied SHA256SUMS.txt against the downloaded package. The attached source-text collection is not a ready-to-run program. *Capture: distribution and checksum verification result.*

2.  **Choose your launch method.** For a supplied Windows installer or executable, use its shortcut or executable. From the source folder on Windows, open run_windows.bat. On Linux, run run_linux.sh using your normal terminal workflow. Source launchers prepare the environment and start app.py. *Capture: launcher and startup output.*

3.  **Wait for the account window.** The first screen is Connect to GitHub unless a usable token is loaded from the optional system keyring. If the window does not open, check startup output rather than opening more copies. *Capture: first account screen with an empty token field.*

## 2.3 Connect your GitHub account

1.  **Prepare a fine-grained personal access token.** Limit it to the repositories and actions you need. The connection screen recommends Metadata read access, with Issues read/write and Administration write only for relevant actions. Organization approval or other permissions may also be needed. *Capture: permission selection only; never the token value.*

2.  **Enter the token in Personal access token.** Leave Remember token using optional system keyring unchecked for session-only use. Selecting it requests storage in the operating system’s keyring. *Capture: connection screen with the entry hidden or blank.*

3.  **Select Connect account.** GCC loads the account, repositories, public activity, and API allowance. Check the connected account indicator and Dashboard. *Capture: Dashboard with non-sensitive repository names.*

4.  **Resolve any error.** Check token expiry, repository access, organization restrictions, connectivity, and API limits. A keyring storage warning may appear even when connection succeeds. *Capture: sanitized error or storage warning.*

## 2.4 Set your local workspace

1.  **Open Settings.** In Local workspace, choose a parent folder for cloned projects. Use Browse for the folder picker. *Capture: Settings and a non-sensitive folder path.*

2.  **Select Save settings.** This saves the clone destination used by the main Repositories screen. Check Git command available: Yes. *Capture: save confirmation and Git availability.*

3.  **Open Local Git, then Choose Repository.** Pick the project folder. GCC asks to initialize it if it is not a Git repository. Accept only when creating a new repository is intentional. *Capture: folder picker, initialization prompt if shown, and repository header.*

## 2.5 Clone an existing project

1.  **Choose the source.** In Repositories, select a repository and use Clone. Alternatively, in Local Git use Clone and enter the repository URL. Git authentication must be configured separately for private repositories. *Capture: selected repository or credential-free URL dialog.*

2.  **Confirm the destination.** Main-window cloning uses the saved workspace; Local Git cloning asks for a parent folder. Wait for the result. *Capture: folder choice where applicable and clone result.*

3.  **Open the cloned folder.** Use Choose Repository after cloning. The Local Git clone function does not automatically select the new repository. Press F5 and check the path and branch. *Capture: refreshed Local Git header and working tree.*

## 2.6 Confirm readiness

1.  **Press Ctrl+K and search Self-Test & Readiness.** Open the matching entry with a repository selected. *Capture: matching Command Palette result.*

2.  **Review the report.** Use Run tests and Export results as needed. A repository without its first commit can fail HEAD or history checks even when Git works. *Capture: report and any failed check.*

3.  **Fix the specific failure.** PASS confirms core command/parser readiness, not every GitHub permission, scanner, signing setup, or linked-worktree scenario. *Capture: corrected report or external-tool readiness evidence.*

## 2.7 Disconnect safely

1.  **Open Settings and select Disconnect and forget token.** GCC clears the current connection and attempts to remove the saved keyring token. This does not revoke it in GitHub or sign gh out. *Capture: disconnect control and return to connection screen.*

2.  **Check your system credential store if removal is uncertain.** Remove any remaining GCC entry manually; revoke the token in GitHub if it should no longer work. *Capture: confirmation only, with secrets hidden.*

# 3. Find your way around

## 3.1 Main account window

| **Area** | **What it does** |
|----|----|
| Dashboard | Shows loaded repository totals, stars, forks, open-issue counts, and recently updated repositories. These are account/repository indicators, not a complete organizational inventory. |
| Repositories | Searches loaded repositories by name, description, or language. Sort choices are Recently updated, Name, and Most stars. Select a row before Create issue, Clone, or Open on GitHub. |
| Local Git | Opens the separate Local Git Workspace for a folder on your computer. |
| Activity | Shows recent public activity for the connected account. It is not a complete private-activity audit. |
| Insights | Shows repositories not updated for more than 90 days, missing descriptions, the language portfolio, and remaining API allowance. |
| Settings | Sets the clone workspace, reports Git availability, and disconnects the account. |

## 3.2 Local Git Workspace

The header identifies the selected repository. The action bar contains Refresh, Stage selected, Stage all, Unstage, Commit, Fetch, Pull safely, and Push. Smart Sync and Pre-Commit Review open guided tools. The Working Tree table lists changed files. The right-side tabs show History, Branches, Stash, Tags, Remotes, and Conflicts.

**Badges:** Branch names your current line of work. Changes counts changed status entries, not changed lines. Sync: +ahead / -behind compares your branch with the locally known upstream. Fetch before treating these values as current. Sync: no upstream means comparison is unavailable; it does not prove that nothing needs publishing.

**Status codes:** the State column uses Git’s two-character status format. The first position describes the staged/index state; the second describes the working-tree state. M means modified, A added, D deleted, R renamed, ?? untracked, and U indicates an unresolved state. A file can have both staged changes and further unstaged edits.

## 3.3 Command Palette: your route to every feature

1.  **Press Ctrl+K in Local Git.** Or select Command Palette / All commands. *Capture: open palette and search field.*

2.  **Type a feature name or related keyword.** For example, search “stash”, “release”, or “reflog”. The palette searches feature names and keywords. *Capture: filtered results.*

3.  **Select the intended entry.** Double-click it, or press Enter with the intended row selected. Check the repository shown in the opened tool before proceeding. *Capture: selected entry and opened tool header.*

**Shortcuts:** Ctrl+K opens Commands; F5 refreshes Local Git; Ctrl+Enter opens the commit message prompt. These bindings belong to the workspace and may not apply inside every child window.

## 3.4 Task groups and older sidebar labels

The supplied navigation model defines Home, Changes, History, Branches, Sync, Review, GitHub, Release, Recover, and Advanced. The legacy workspace code also builds WORK, COLLABORATE, QUALITY, and TOOLS. These are ways to organize the same broad work, but the source does not establish that every newer model label is wired into the visible sidebar. Follow the exact palette names in this guide if a sidebar item is missing.

## 3.5 Reading wide tables in v3.53

Version 3.53 normalizes table cells to a single visual line, expands columns to fit content within a cap, and adds horizontal scrolling for wide tables. Scroll sideways to read long file names or results. Help/status labels wrap within their own area. “Completed successfully.” is a status message, not a changed-file entry; if it appears split across State and File, check that the corrected v3.53 build is running.

# 4. Your First Working Day

**Illustrative example:** make a small documentation change on a practice branch such as docs/update-readme. Example names in this guide are not instructions to change a real production branch.

## 4.1 Start from a known state

1.  **Choose Repository and press Refresh or F5.** Confirm the folder, branch, and changed-file list. Stop if you opened the wrong project. *Capture: header, badges, and Working Tree.*

2.  **Fetch before comparing with the remote.** The workspace Fetch runs fetch for all remotes with pruning. Use Fetch Preview first if you want to inspect potential remote-tracking reference changes. Fetch does not merge downloaded commits into your branch. *Capture: fetch preview where used and fetch result.*

3.  **If your branch is only behind, use Pull safely.** This uses fast-forward-only pull. It refuses histories that require a merge or rebase; do not treat refusal as permission to force anything. *Capture: pull result and updated Sync badge.*

## 4.2 Create a branch and edit files

1.  **Open the Branches tab and select New.** Enter a meaningful name. The workspace creates and switches to the branch. *Capture: New branch dialog and updated Branch badge.*

2.  **Edit the project using your normal editor.** Open folder can help you find it. Save your files, return to GCC, and press F5. GCC is not a full source-code editor. *Capture: saved example edit and refreshed changed-file list.*

## 4.3 Review, stage, and commit

1.  **Select a changed file and use View diff.** The workspace diff shows unstaged changes. For staged content or a clearer comparison, open Visual Diff Center. New untracked files may need separate inspection or whole-file staging. *Capture: selected file and its diff.*

2.  **Select Stage selected for the intended files.** Stage all includes all changes, so use it only after reviewing every item. Staging a file captures its current content; later edits require another staging action. *Capture: selected files and staged status.*

3.  **Check the staged version.** Open Visual Diff Center and choose Staged, or use Pre-Commit Review. Make sure no credentials, generated files, or unrelated work are included. Use Unstage to remove an item from the next commit without deleting its file changes. *Capture: staged diff and review results.*

4.  **Select Commit or press Ctrl+Enter.** Enter a short message explaining the change. An illustrative message is “docs: clarify first-run setup”. Commit records only staged changes. *Capture: commit prompt and success or hook result.*

5.  **Refresh and inspect History.** Confirm the new commit appears. A clean tree is expected only if you committed all changes; intentionally unstaged work can remain. *Capture: new history entry and remaining working-tree state.*

## 4.4 Publish your branch

1.  **Fetch and run Preflight Quality Gates.** Review outgoing commits, required checks, and upstream state before sending anything. *Capture: preflight report and branch comparison.*

2.  **Use Remote Branch Center for a branch without an upstream.** Publish the intended local branch to the intended remote and establish tracking using that tool’s explicit workflow. Confirm names before executing. *Capture: publish/tracking inputs and result.*

3.  **Use Push for ordinary updates.** If rejected, fetch and inspect Pull Strategy Advisor or Upstream Health. Do not switch to Force-with-Lease merely to make the error disappear. *Capture: push result and updated branch state.*

# 5. Manage Changes Without Losing Work

## 5.1 Stage only part of a file

1.  **Open Ctrl+K → Visual Diff Center.** Choose Working tree, optionally set a path filter, and select Refresh. Changing the mode or algorithm needs a refresh to reload the comparison. *Capture: mode, filter, and file list.*

2.  **Select the file, then the hunk.** Read the side-by-side comparison and word-level highlighting. Check that the block contains only the change you want in this commit. *Capture: selected file, hunk, and comparison.*

3.  **Select Stage hunk and confirm.** Switch to Staged and Refresh to check the result. To reverse it, select the staged hunk, use Unstage hunk, and confirm. *Capture: confirmation and staged or unstaged result.*

4.  **Use whole-file staging when appropriate.** Binary, new untracked, or inseparable patch changes may not offer usable text hunks. Inspect the file separately and use Stage selected in the workspace or Stage whole file in Partial Staging. *Capture: no-hunk message and whole-file staged result.*

Partial Staging is the older dedicated hunk tool. Its Unstage selected hunk opens a separate dialog listing staged hunks. Select and preview the intended hunk there before unstaging. Neither tool provides a general arbitrary line-selection editor.

## 5.2 Put unfinished work aside with a stash

1.  **Refresh and review the files you are putting aside.** For all ordinary changes, use the Stash tab’s Save stash and enter a helpful message. This action includes untracked files but is not a backup of all ignored files. *Capture: changed files and stash message.*

2.  **Confirm the stash appears.** Check the Stash tab or Stash Manager Pro and inspect the stored change before changing tasks. *Capture: stash entry and inspected diff.*

3.  **Bring the work back deliberately.** Prefer Apply in Stash Manager Pro first if you want to keep the saved entry until you have checked the result. Pop attempts to apply and remove the entry on success; Drop deletes it. *Capture: selected stash, chosen action, and result.*

4.  **Resolve any conflict before continuing.** A stash application can conflict with the current branch. Refresh, inspect the conflict files, and confirm whether the stash entry still exists. *Capture: conflict state and stash list.*

Use Selective Stash when only particular paths should be put aside, and review options for untracked files or keeping staged changes. Do not assume a stash is available in another clone.

## 5.3 Merge a branch into your current branch

1.  **Switch to the destination branch.** Save unfinished work first. Fetch and confirm that this is the branch intended to receive the changes. *Capture: destination branch and refreshed state.*

2.  **Use Merge Preview Center or Compare & Review.** Select the source and target refs and inspect likely changes. A preview is information, not approval and not a guarantee that every later merge succeeds. *Capture: chosen refs and preview.*

3.  **In the Branches tab, select Merge.** Enter the branch to merge into the current branch and read the confirmation. Check the result; if conflicts appear, follow the next workflow. *Capture: merge prompt and result.*

4.  **Run tests and review History.** Verify the intended files and commits before pushing the integrated result. *Capture: final diff/history and test evidence.*

## 5.4 Resolve a conflict

1.  **Open Ctrl+K → Resolve merge conflicts.** Select the file. The panes show OURS, MERGED RESULT, and THEIRS. Use Conflict Stage Explorer when the base/ours/theirs meaning is unclear. In a rebase, “ours” and “theirs” may not mean your original feature branch versus someone else’s branch. *Capture: conflicted file and all comparison panes.*

2.  **Prepare the merged result.** Edit the middle pane to keep the right content and remove conflict markers. Use ours or Use theirs replaces the entire file version after confirmation; it does not selectively solve each block. *Capture: edited result or replacement confirmation.*

3.  **Choose Save + mark resolved.** Save alone writes the file but does not stage resolution. Repeat for every conflict and review staged changes. This text-based editor is not suitable for resolving arbitrary binary files. *Capture: saved/staged resolution and remaining conflicts.*

4.  **Finish the operation that caused the conflict.** For a merge, commit the staged resolution. For rebase, cherry-pick, revert, or patch application, use that tool’s Continue workflow. The resolver’s Abort merge button is for a merge, not a universal abort. *Capture: correct Continue or commit action and final state.*

5.  **Test the result.** A file with no conflict markers can still be logically wrong. Run your project’s checks before pushing. *Capture: test result and clean conflict list.*

## 5.5 Discard and clean: different kinds of deletion

1.  **Decide what you really want.** Unstage keeps edits. Discard selected restores tracked working-file content from the index, so staged changes can remain. Clean targets untracked files or folders. Hard reset can also discard staged tracked changes. *Capture: relevant status and proposed action.*

2.  **Preview exact paths.** Use Safe Clean Center or Selective Clean before deleting untracked content. Ordinary workspace Clean preview shows the untracked items before confirmation; ignored-file cleaning is a separate, more dangerous option in specialist tools. *Capture: complete deletion preview.*

3.  **Back up anything you may need, then confirm only the intended deletion.** Git usually cannot recover untracked or uncommitted content that was never stored. Refresh afterward and check that expected files remain. *Capture: confirmation and refreshed file inventory.*
