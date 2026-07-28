---
name: test-schedule
description: Test an available Scheduled Job Task Prompt by invoking schedule-workspace first, asking which schedule should be tested, and running the AFK Research CLI schedule run command with the selected slug. Use when the user asks to test, smoke test, run, validate, or verify that a schedule or Scheduled Job runs properly.
disable-model-invocation: true
---

# Test Schedule

## Core Rule

Run an existing Task Prompt through the project CLI. This executes the selected agent runner without an interactive approval flow, so inspect the Task Prompt first and do not run obviously destructive or unclear work without explicit user confirmation.

## Startup

1. Follow repo instructions first. If root `AGENTS.md` requires `/query`, ask `.brain` for relevant schedule and safety context before running anything.
2. Invoke `schedule-workspace` first:
   - Read and apply `.agents/skills/schedule-workspace/SKILL.md` when it exists.
   - Follow its startup sequence, including `.schedule/AGENTS.md` and `.schedule/tasks/` inspection.
3. If `.schedule` does not exist, say the project has no initialized Schedule Workspace and stop unless the user asks to initialize scheduled jobs.
4. Run `npx afk-research schedule list` to inspect existing Task Prompts.

## Test Flow

1. If no Task Prompts exist, say there are no schedules to test and stop.
2. If the user did not name a schedule, list available slugs and ask which schedule should be tested.
3. Run `npx afk-research schedule read <slug>`.
4. Confirm it declares `runner: codex` or `runner: claude`, has expected trigger cadence/time/time zone metadata when the schedule should be recurring, has a non-empty body, and is bounded enough for unattended execution.
5. Show the selected slug, runner, prompt summary, declared write scope, and explain that the CLI will make one minimal model call in an isolated temporary directory to verify the selected runner before making the actual task call.
6. Ask for explicit confirmation before every manual run, including report-only tasks.
7. Run the CLI from the project root:

```sh
npx afk-research schedule run <slug>
```

When targeting a different project directory, use:

```sh
npx afk-research schedule run <slug> --path /absolute/path/to/project
```

## Reporting

Report the command run, whether it exited successfully, and the important stdout or stderr. If Runner Readiness Verification reports a missing Codex or Claude Code CLI, provide installation guidance and leave the Task Prompt unchanged. If it reports an authentication failure, offer to run `codex login` or `claude auth login` for the Task Prompt's selected runner. After an approved login flow, retry `schedule run` once; do not loop. Never request, read, copy, or store credentials.
