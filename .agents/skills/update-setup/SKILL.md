---
name: update-setup
description: Update an existing AFK Research setup from the selected Update Source by guiding the user through a CLI-owned dry run, confirmation, apply, verification, and changed-file report. Use when the user asks to update AFK Research setup files, refresh bundled project skills, install the latest AFK skills from the remote source, or sync the local setup from source.
disable-model-invocation: true
---

# Update Setup

## Core Rule

Use the AFK Research CLI as the updater implementation. Do not manually copy skills, templates, prompts, `.brain` schema files, Claude files, docs, or manifest entries from the Update Source into the target project.

A Setup Update refreshes AFK-managed files, Bundled Project Skills, and the target project's local AFK CLI package from an Update Source while preserving user-edited files and Local Project Skills. By default it preserves the Setup Features recorded in the AFK manifest; only pass feature flags when the user explicitly asks to add or remove Claude Code support, Design Workspace, Schedule Workspace, or Sandcastle support.

## Preconditions

1. Locate the target project.
   - Recommend the current repository root when the user is already working inside the project.
   - If the agent appears to be inside the AFK Research source repository or a parent directory, ask the user to confirm the target path before continuing.
2. Check whether `.agents/afk-research-manifest.json` exists in the target project.
   - If it is missing, tell the user that update can continue only through CLI-owned Manifest Recovery. Ask for confirmation before adding `--recover-manifest` to the dry-run and apply commands. Do not create or edit the manifest by hand, do not fall back to manual copying, and do not rerun setup as a substitute.
3. Check prerequisites from the target environment:

```sh
node --version
npm --version
git --version
```

4. Choose the Update Source.
   - Default: `github:RTTJogja/afk-research`.
   - Use a different package spec or local path only when the user explicitly asks for a fork, branch, or local development source.
5. Inspect the target worktree when it is inside Git:

```sh
git -C "<target>" status --short --branch
```

If there are existing changes, summarize them before the dry run. Do not stage, commit, reset, or revert them.

## Dry Run

If the user explicitly asked to add or remove Setup Features, include only the requested feature flags:

```sh
--claude | --no-claude
--design | --no-design
--schedule | --no-schedule
--sandcastle | --no-sandcastle
```

If Manifest Recovery was confirmed, include:

```sh
--recover-manifest
```

Build the dry-run command with the selected Update Source:

```sh
npx --yes --package "<update-source>" afk-research update "<target>" --yes --dry-run --source "<update-source>" [--recover-manifest] [feature flags]
```

Show the exact command to the user, then run it.

If the command fails because `afk-research update` is not available in that source, stop and report that the selected AFK Research CLI does not support Setup Update yet. Do not manually update files.

Summarize the dry-run output, including:

- Target project.
- Update Source.
- Whether the manifest came from the existing manifest file or Manifest Recovery.
- Current Setup Features.
- Requested Setup Feature changes, if any.
- Resulting Setup Features.
- File action counts.
- Dependency commands that will run, including AFK CLI refresh and Sandcastle install or uninstall when applicable.
- Bundled Project Skills that will be created, updated, unchanged, conflicted, or retired.
- Local Project Skills that will be preserved.
- Conflicts and generated sidecar files.
- Warnings.

Ask the user to confirm before applying the update. If the user does not confirm, stop without changing files.

## Apply

After confirmation, run the same command without `--dry-run`:

```sh
npx --yes --package "<update-source>" afk-research update "<target>" --yes --source "<update-source>" [--recover-manifest] [feature flags]
```

If the command fails, report the exact failing command and the relevant error output. Do not repair files manually unless the user separately asks for an implementation fix.

## Verification

Read the CLI-owned Setup Update or Installation Verification summary from the command output.

If verification passed, summarize the pass result. If verification failed, report the failed CLI checks verbatim, including expected and actual values when shown. Do not maintain a separate prompt-side checklist for required files, directories, package dependencies, manifest readability, or command outcomes.

## Changed Files

After apply, show the generated or changed files. If the target is inside a Git worktree, use:

```sh
git -C "<target>" status --short
```

End by telling the user that the Setup Update is complete and that generated files should be reviewed before committing. Do not create a commit unless the user explicitly asks.

## Safety Rules

- Reuse the setup choices recorded in `.agents/afk-research-manifest.json`.
- Do not ask about or enable new optional feature families by default.
- Use `--recover-manifest` only after explicit user confirmation when the manifest is missing.
- Do not create or edit the AFK manifest by hand.
- Do not delete Local Project Skills.
- Retire a Bundled Project Skill only when the manifest proves the local copy is still installer-owned.
- Preserve user-edited managed files by relying on Managed File Reconciliation and conflict sidecars.
- Do not commit, push, reset, revert, or clean the worktree unless the user explicitly asks.
