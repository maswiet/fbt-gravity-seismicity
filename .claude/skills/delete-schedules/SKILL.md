---
name: delete-schedules
description: Delete selected or all schedules by invoking schedule-workspace first, asking whether to delete all schedules or particular schedules from the available list, and using the CLI to remove project Task Prompts and notify a live Schedule Runner. Use when the user asks to remove, delete, clear, or clean up schedules, Scheduled Jobs, recurring tasks, or schedule Task Prompts.
disable-model-invocation: true
---

# Delete Schedules

## Core Rule

Delete schedules through the AFK Research CLI only. `npx afk-research schedule delete` removes the selected project Task Prompt files and reconciles a live Schedule Runner. Do not delete `.schedule/tasks/*.md` directly unless the CLI is unavailable and the user explicitly approves a fallback.

## Startup

1. Follow repo instructions first. If root `AGENTS.md` requires `/query`, ask `.brain` for relevant schedule context before planning or editing.
2. Invoke `schedule-workspace` first:
   - Read and apply `.agents/skills/schedule-workspace/SKILL.md` when it exists.
   - Follow its startup sequence, including `.schedule/AGENTS.md` and `.schedule/tasks/` inspection.
3. If `.schedule` does not exist, say the project has no initialized Schedule Workspace and stop unless the user asks to initialize scheduled jobs.
4. Run `npx afk-research schedule list` to inspect existing Task Prompts.

## Delete Flow

1. If no Task Prompts exist, say there are no schedules to delete and stop.
2. Ask whether the user wants to delete all schedules or particular schedules from the available list.
3. For particular schedules, ask for the exact slug or slugs and verify each exists in the CLI list output.
4. For all schedules, ask for explicit confirmation before deleting every Task Prompt in the project.
5. Run the CLI only after confirmation:

```sh
npx afk-research schedule delete <slug> --yes
```

For all schedules:

```sh
npx afk-research schedule delete --all --yes
```

6. Read the CLI output and report deleted Task Prompt slugs and the live Schedule Runner reconciliation result.
7. Run `npx afk-research schedule list` afterward and report any remaining schedules.
