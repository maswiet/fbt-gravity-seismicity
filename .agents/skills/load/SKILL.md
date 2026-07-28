---
name: load
description: Pull the latest changes from a configured git remote into the current local repository. Use when the user asks to load, pull, sync, update, fetch latest, get remote changes, or bring the local repo up to date from the remote repository.
disable-model-invocation: true
---

# Load

## Core Rule

A Repository Load brings the current branch up to date from its configured remote without creating commits, changing remotes, or overwriting unsaved local work.

## Workflow

1. Locate the repository root with `git rev-parse --show-toplevel`.
   - If this fails, stop and explain that `/load` must run inside a git repository.
2. Inspect the working tree with `git status --short --branch`.
   - If there are merge conflicts or unmerged paths, stop before fetching and tell the user to resolve them first.
   - If there are tracked, modified, deleted, or untracked files, stop before pulling. Tell the user to save, commit, stash, or discard those changes before rerunning `/load`.
3. Confirm a pull target.
   - Prefer the current branch upstream from `git rev-parse --abbrev-ref --symbolic-full-name @{u}`.
   - If there is no upstream but `origin` has a fetch URL and the current branch exists on `origin`, use `origin <current-branch>`.
   - If there is no usable remote branch, stop and tell the user to configure an upstream or remote branch before rerunning `/load`.
4. Record the current commit with `git rev-parse --short HEAD`.
5. Fetch the selected remote with `git fetch --prune <remote>`.
6. Pull with fast-forward only.
   - With an upstream, run `git pull --ff-only`.
   - Without an upstream but with a valid `origin/<current-branch>`, run `git pull --ff-only origin <current-branch>`.
7. Record the final commit with `git rev-parse --short HEAD` and inspect `git status --short --branch`.
8. Report the branch, pull target, before and after commit, whether anything changed, and any remaining status output.

## Divergence And Pull Failures

If `git pull --ff-only` fails because the local and remote branches diverged, stop and report that the repository needs an explicit merge or rebase decision. Do not run `git merge`, `git rebase`, `git reset`, or conflict resolution commands unless the user explicitly asks.

If fetch or pull fails because of authentication, network problems, missing refs, or permissions, keep the working tree unchanged and report:

- The pull target.
- The exact command that failed.
- The exact error summary.
- A practical next command, such as `gh auth status`, `gh auth login`, `git remote -v`, or the same fetch/pull command after fixing access.

## Safety Rules

- Do not create, remove, rename, or reconfigure remotes.
- Do not stage, commit, stash, discard, reset, merge, or rebase changes unless the user explicitly asks.
- Do not pull into a dirty or conflicted working tree.
- Do not push as part of `/load`.
- Do not continue after a failed fetch or pull; report the blocker and the rerun command.
