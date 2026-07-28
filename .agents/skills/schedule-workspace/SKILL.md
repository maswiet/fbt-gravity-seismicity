---
name: schedule-workspace
description: Refocus AI Agent onto a project's `.schedule` Schedule Workspace for Scheduled Job prompts, runner selection, Schedule Runner lifecycle guidance, and unattended execution safety rules. Use when the user asks to create, inspect, edit, run, or reason about scheduled jobs, task prompts, or schedule-related project automation.
disable-model-invocation: true
---

# Schedule Workspace

## Core Rule

Use `.schedule` as the default working scope for Scheduled Job tasks. Preserve higher-priority repo instructions, but search, read, and edit Schedule Workspace files before expanding to repository-level files.

## Startup

1. Read the root `AGENTS.md` if present.
2. If `.brain/AGENTS.md` exists, read it before using `.brain`; follow it for second-brain queries, notes, logs, and durable knowledge.
3. Locate the nearest `.schedule` directory from the current workspace or repository root.
4. If `.schedule/AGENTS.md` exists, read it and treat it as the operating guide for Scheduled Job contents.
5. Inspect `.schedule/tasks/` for available Task Prompts before creating or running jobs.

If `.schedule` does not exist, say that the project has no initialized Schedule Workspace. Do not create one unless the user explicitly asks to initialize scheduled jobs.

## Working Pattern

- Treat `.schedule` as the task workspace: run targeted searches there first and keep Task Prompts under `.schedule/tasks/`.
- Use `npx afk-research schedule list`, `read`, `create`, `update`, and `delete` for schedule CRUD. Do not edit `.schedule/tasks/*.md` directly unless the CLI is unavailable and the user explicitly approves a fallback.
- Task Prompt slugs use lowercase kebab-case.
- Each Task Prompt must declare `runner: codex` or `runner: claude`; the CLI writes this frontmatter during create/update.
- Recurring Task Prompts should also carry CLI-written `trigger_time` in `HH:MM` 24-hour format, an IANA `timezone`, and `trigger_interval_days` for the cadence or gap. Use `--daily`, `--weekly`, or `--every-days N`.
- Use `npx afk-research schedule run <task-slug>` to run a Task Prompt; do not pass arbitrary file paths.
- Use `npx afk-research schedule read <task-slug>` to inspect portable Task Prompt metadata.
- Use `npx afk-research schedule delete <task-slug> --yes` to remove a schedule from the project and notify a live Schedule Runner.
- Use the explicit `start-schedule-runner`, `stop-schedule-runner`, and `check-schedule-runner-status` skills for runner lifecycle work.
- Scheduled Jobs run without an interactive approval flow. Keep prompts trivial, bounded, and explicit about whether writes are allowed.
- Use repository-level files only when needed for project context, implementation, tests, or commands that must run from the project root.

## Creation Boundary

When the user explicitly asks to create or add Scheduled Job support:

1. Prefer the project's own setup command, usually `afk-research init --schedule`, when available.
2. Preserve user-provided task intent; derive only lowercase kebab-case storage slugs when needed.
3. Leave `.schedule/tasks/` empty during setup unless the user asks for a specific Task Prompt.
4. Use `npx afk-research schedule create <slug> --runner codex --trigger-time 09:00 --timezone Asia/Jakarta --weekly --prompt-file <file>` after the user asks for a specific Task Prompt.
5. Use `schedule update` for Task Prompt or trigger changes and `schedule delete` for complete schedule removal. These commands notify a live Schedule Runner and recalculate its project-level Host Wake Entry without running jobs immediately.

## Completion

Report which `.schedule` files were read or changed, whether `.brain` was consulted or updated, and any cases where work had to expand beyond the Schedule Workspace.
