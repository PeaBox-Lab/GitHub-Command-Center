# GitHub Command Center 1.0 User Guide

## Daily workflow
1. Connect your GitHub account from Settings if you need account-level APIs.
2. Open Local Git and select your repository.
3. Review changed files and diffs.
4. Stage selected files and commit.
5. Fetch, then use FF-only Pull.
6. Compare your branch with the target branch before opening a PR.
7. Push and use Pull Requests to create or manage the PR.
8. Check Actions for CI results.

## Conflict workflow
Open Resolve conflicts. Review OURS and THEIRS, edit MERGED RESULT, save and mark each file resolved. Commit after every conflict has been staged.

## Release workflow
Use Health and Security first. Open Compare for a pre-release review. Then use Release Center to run readiness checks, generate notes, create/push the tag, attach assets and publish. Create a bundle/checksum for recovery and verification.

## Recovery workflow
Before rebase/reset or other risky operations, create a Recovery checkpoint. Full `.bundle` files can recreate the repository offline.

## Multi-repository workflow
Use Repo Manager to scan a parent workspace, identify repositories with local changes or remote divergence, fetch selected repositories, then open an individual repository for detailed work.
