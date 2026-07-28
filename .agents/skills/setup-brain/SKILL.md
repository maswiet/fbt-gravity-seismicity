---
name: setup-brain
description: Initialize, repair, or upgrade the repository-local `.brain` second brain schema and brain-transfer output ignore rules. Use when the user asks to set up `.brain`, create a second brain, repair missing brain files or folders, or make an existing `.brain` match this repo's brain conventions.
disable-model-invocation: true
---

# Setup Brain

## Core Rule

Create or repair the repository-local Second Brain additively, and ensure generated brain-transfer artifacts under `.outputs/` are ignored by Git. Never delete existing `.brain` content, never overwrite existing schema or wiki files without explicit approval, and publish `.brain` changes after setup.

## Workflow

1. Read workspace `AGENTS.md` files that apply to the current repo.
2. If `.brain/AGENTS.md` exists, read it as the current authoritative schema.
3. Run the helper script from the repository root:

```bash
python3 .agents/skills/setup-brain/scripts/setup_brain.py
```

4. Review the script output. It creates missing standard folders and missing seed files only, and appends `.outputs/` to `.gitignore` when missing; existing files are otherwise left unchanged.
5. If the script reports no `.brain` changes, say no `.brain` repository publish was needed.
6. If `.brain` changed, run `git status --short`, stage only this setup's `.brain` changes, commit with `brain: setup second brain`, and push the current branch to its upstream. If no upstream is configured and `origin` exists, use `git push -u origin HEAD`.
7. Report any `.gitignore` change separately as a normal repository setup change.

## Standard Vault Shape

The setup helper ensures these roots and files exist:

- `.brain/AGENTS.md`
- `.brain/CLAUDE.md`
- `.brain/raw/`
- `.brain/wiki/index.md`
- `.brain/wiki/log.md`
- `.brain/wiki/{sources,concepts,entities,claims,questions,syntheses,outputs,templates,inbox,scratch,archive}/`
- Basic templates under `.brain/wiki/templates/`
- `.gitignore` entry for `.outputs/`

## Repair Rules

- Treat existing `.brain/AGENTS.md` as authoritative.
- Create missing directories and seed files.
- Do not replace an existing `AGENTS.md`, `CLAUDE.md`, `index.md`, `log.md`, or template file.
- Append a setup log entry when the script changes the vault and a log file exists or is created.
- Append `.outputs/` to `.gitignore` when missing, creating `.gitignore` if needed.
- Keep vault content inside `.brain`; the only repo-level setup edit is the `.outputs/` `.gitignore` entry.
