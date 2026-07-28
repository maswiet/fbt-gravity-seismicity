---
name: read-design
description: Use AFK Research CLI commands to list available Design Systems or read a selected Design System inside a project's `.design` Design Workspace. Use when the user asks to read, view, inspect, list, show, summarize, or open Design Workspace guidance, `DESIGN.md`, design tokens, Tailwind design config, templates, examples, or available Design Systems.
---

# Read Design

## Core Rule

Invoke `design-workspace` first, then use the project CLI. Keep the operation read-only.

In this skill, "Design" means a project Design System under `.design/design-system/`, not the whole Design Workspace. Do not implement a chat menu or manually inspect `.design/design-system/` unless the CLI is unavailable.

## Startup

1. Follow repository instructions first. If they require `$query`, ask the `.brain` wiki for relevant design, domain, constraints, and open questions before planning.
2. Invoke `design-workspace`:
   - Read and apply `.agents/skills/design-workspace/SKILL.md` when it exists.
   - Follow its startup sequence, including root `AGENTS.md`, `.brain/AGENTS.md` when relevant, `.design/AGENTS.md`, and `.design/design-system/` inspection.
3. Use CLI-owned Design System operations:

```bash
afk-research design list --path .
afk-research design read "<Design System Name or Slug>" --path .
```

When working outside the repository root, pass that repository path to `--path`.

## List Design Systems

For list/read-discovery requests, run:

```bash
afk-research design list --path .
```

Use `--json` when another tool or a precise machine-readable result would help:

```bash
afk-research design list --path . --json
```

## Read A Selected Design System

If the user named a Design System, run:

```bash
afk-research design read "<Design System Name or Slug>" --path .
```

If the user did not name a Design System, run `afk-research design read --path .`. The CLI auto-selects only when exactly one Design System is available. If multiple systems exist, report the CLI's resolver error and ask for an exact Design System Name or Slug. Do not present a menu.

Use `--json` when you need structured file contents:

```bash
afk-research design read "<Design System Name or Slug>" --path . --json
```

Summarize the CLI output for the user unless they asked for exact file contents.

## Completion

Report:

- the CLI command used
- the selected Design System, if any
- `.design` files reported by the CLI
- whether `.brain` was consulted or updated

Do not automatically commit or push. Reading Design Workspace files is not a repository publish operation.
