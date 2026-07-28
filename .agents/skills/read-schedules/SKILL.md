---
name: read-schedules
description: List or inspect Scheduled Job Task Prompts in `.schedule/tasks/` after invoking schedule-workspace first. Use when the user asks to read schedules, list schedules, show available scheduled jobs, inspect a specific schedule, or review schedule Task Prompt details.
disable-model-invocation: true
---

# Read Schedules

## Core Rule

Read Schedule Workspace Task Prompts through the AFK Research CLI. Do not read `.schedule/tasks/*.md` directly unless the CLI is unavailable and the user explicitly approves a fallback. Do not run schedules or change runner state while reading.

## Startup

1. Follow repo instructions first. If root `AGENTS.md` requires `/query`, ask `.brain` for relevant schedule context before answering.
2. Invoke `schedule-workspace` first:
   - Read and apply `.agents/skills/schedule-workspace/SKILL.md` when it exists.
   - Follow its startup sequence, including `.schedule/AGENTS.md` and `.schedule/tasks/` inspection.
3. If `.schedule` does not exist, say the project has no initialized Schedule Workspace and stop unless the user asks to initialize scheduled jobs.

## Read Flow

1. Run `npx afk-research schedule list`.
2. If no Task Prompts exist, say there are no schedules in the Schedule Workspace.
3. If the user did not specify a mode, ask whether they want to list all schedules or read a particular schedule. Include the available slugs in the question.
4. For a list request, show the CLI list output: slug, runner, and portable Task Prompt metadata.
5. For a specific schedule, verify the requested slug exists, then run `npx afk-research schedule read <slug>` and summarize its runner, Task Prompt path, trigger metadata, purpose, write permissions, and any output/log expectations.

## Boundaries

- Treat schedule names as slugs, not arbitrary file paths.
- Keep reads on the CLI surface unless the user asks for broader project context.
- Use `check-schedule-runner-status` when the user wants operational state rather than Task Prompt definitions.
