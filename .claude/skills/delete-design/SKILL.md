---
name: delete-design
description: Use AFK Research CLI commands to delete a selected Design System or all Design Systems from a project's `.design/design-system/` folder. Use when the user asks to delete, remove, purge, or clean up a Design System or all Design Systems in a Design Workspace.
---

# Delete Design

## Core Rule

Invoke `design-workspace` first, then use `afk-research design delete`. Do not implement deletion with a chat menu, custom shell deletion, or manual filesystem removal.

`design delete` deletes Design System directories under `.design/design-system/` and preserves the Design Workspace container. Do not treat this skill as Setup Feature Removal.

## Startup

1. Follow repository instructions first. If they require `$query`, ask the `.brain` wiki for relevant design, domain, constraints, and open questions before planning.
2. Invoke `design-workspace`:
   - Read and apply `.agents/skills/design-workspace/SKILL.md` when it exists.
   - Follow its startup sequence, including root `AGENTS.md`, `.brain/AGENTS.md` when relevant, `.design/AGENTS.md`, and `.design/design-system/` inspection.
3. Use the CLI for all selection and deletion behavior:

```bash
afk-research design list --path .
afk-research design delete "<Design System Name or Slug>" --path . --dry-run
afk-research design delete "<Design System Name or Slug>" --path . --yes
```

When working outside the repository root, pass that repository path to `--path`.

## Delete A Selected Design System

If the user named a Design System, preview first:

```bash
afk-research design delete "<Design System Name or Slug>" --path . --dry-run
```

Then apply only when the user clearly requested deletion of that target:

```bash
afk-research design delete "<Design System Name or Slug>" --path . --yes
```

Use `--json` when a structured result is useful.

## Delete All Design Systems

For an all-delete request, preview first:

```bash
afk-research design delete --all --path . --dry-run
```

Then apply only when the user clearly requested deleting all Design Systems:

```bash
afk-research design delete --all --path . --yes
```

If the user did not specify a target or `all`, run `afk-research design list --path .` and ask for an exact Design System Name, Design System Slug, or `all`. Do not offer a menu or infer a target.

## Verification

After applying deletion, run:

```bash
afk-research design list --path .
```

## Completion

Report:

- CLI commands used
- Design Systems deleted
- verification performed
- whether `.brain` was consulted or updated
- any CLI errors or skipped targets

Do not automatically commit or push. Design Workspace changes have no special repository publish rule.
