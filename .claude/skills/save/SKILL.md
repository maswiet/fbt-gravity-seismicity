---
name: save
description: Commit and push the current repository changes to a configured remote repository. Use when the user asks to save, commit and push, publish latest changes, or preserve the current repo state in git.
disable-model-invocation: true
---

# Save

## Core Rule

A Repository Save is complete only after the current repository changes are committed locally and pushed to a configured remote repository. Do not create, choose, or configure a remote repository for the user.

## Workflow

1. Locate the repository root with `git rev-parse --show-toplevel`.
   - If this fails, stop and explain that `/save` must run inside a git repository.
2. Inspect the working tree with `git status --short --branch`.
   - If there are merge conflicts or unmerged paths, stop before staging anything and tell the user to resolve them first.
   - If there are no tracked, modified, deleted, or untracked files, report that the working tree is clean and no save was needed.
3. Confirm a push target before committing.
   - If the current branch has an upstream, plan to use `git push`.
   - If no upstream exists but `origin` has a push URL, plan to use `git push -u origin HEAD`.
   - If no usable remote exists, stop before staging or committing. Tell the user to authenticate and configure the remote themselves, then rerun `/save`.
4. Stage all current non-ignored repository changes with `git add -A`.
5. Commit the staged changes.
   - Use a commit message supplied by the user when present.
   - Otherwise use `save: latest changes`.
   - If `git commit` reports that there is nothing to commit, report that no save was needed.
6. Push the commit with the planned push command.
7. Report the branch, commit hash, push command used, and push result.

## Missing Remote Guidance

When no usable remote exists, do not create a remote automatically. Give concise, concrete setup guidance instead:

```sh
gh auth login
gh repo create <owner>/<repo-name> --source=. --remote=origin
git push -u origin HEAD
```

If the remote repository already exists, guide the user to add it instead:

```sh
git remote add origin <remote-url>
git push -u origin HEAD
```

Then tell the user to rerun `/save`.

## Authentication And Push Failures

If the push fails because of authentication, permissions, network problems, or remote rejection, keep the local commit intact and report:

- The commit hash that still needs to be pushed.
- The exact push command that failed.
- The exact error summary.
- A practical next command, such as `gh auth status`, `gh auth login`, or the same `git push` command after fixing access.

Do not amend, reset, revert, or delete the commit unless the user explicitly asks.

## Safety Rules

- Stage all non-ignored repository changes with `git add -A`; do not stage ignored files unless the user explicitly asks.
- Do not create repositories, add remotes, change remote URLs, or choose repository visibility for the user.
- Do not run destructive git commands such as `git reset --hard`, `git checkout --`, or history rewrites.
- Do not push tags unless the user explicitly asks.
- Do not continue after failed staging, commit, or push; report the blocker and the rerun command.
