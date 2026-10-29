# GitHub Command Center v3.6.0

Version 3.6 bundles four practical Git capabilities focused on recurring conflicts, remote branches, repository rules and large-repository cloning.

## Recorded Conflict Resolution (rerere)
- Enable `rerere.enabled`
- Optional `rerere.autoupdate`
- Review rerere status and remaining conflicts
- Re-run recorded resolution processing
- Forget a saved resolution for selected paths
- Clear the rerere cache with confirmation

## Remote Branch Center
- Unified local/remote branch inventory with upstream and ahead/behind counts
- Fetch/prune
- Create a local tracking branch from a remote branch
- Publish the current branch and set upstream
- Rename local branches
- Delete a server-side branch only after exact typed confirmation

## Ignore & Attributes Studio
- Edit `.gitignore` and `.gitattributes` together
- Test ignore rules using `git check-ignore -v --no-index`
- Inspect attributes using `git check-attr -a`
- Add Python ignore defaults and common binary/text attribute defaults

## Advanced Clone Wizard
- Full or shallow clone with configurable depth
- Optional branch and single-branch clone
- No-checkout mode
- Partial clone using `--filter=blob:none`
- Recursive submodules
- Destination-folder picker and command output

All v0.1-v3.5 features remain included through the Command Palette. Versioning remains decimal within major version 3.
