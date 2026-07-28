---
name: update-schedule
description: Update an existing Scheduled Job Task Prompt under `.schedule/tasks/` by invoking schedule-workspace first, asking which schedule to update, and using grill-with-docs to sharpen the change. Use when the user asks to edit, revise, rename, refine, or update an existing schedule, Scheduled Job, recurring task, or schedule Task Prompt.
disable-model-invocation: true
---

# Update Schedule

## Core Rule

Update one existing Task Prompt through the AFK Research CLI. Do not write `.schedule/tasks/*.md` directly unless the CLI is unavailable and the user explicitly approves a fallback.

## Startup

1. Follow repo instructions first. If root `AGENTS.md` requires `/query`, ask `.brain` for relevant schedule, domain, and safety context before planning or editing.
2. Invoke `schedule-workspace` first:
   - Read and apply `.agents/skills/schedule-workspace/SKILL.md` when it exists.
   - Follow its startup sequence, including `.schedule/AGENTS.md` and `.schedule/tasks/` inspection.
3. If `.schedule` does not exist, say the project has no initialized Schedule Workspace and stop unless the user asks to initialize scheduled jobs.
4. Run `npx afk-research schedule list` to inspect available Task Prompts.

## Selection

- If the user named a schedule, verify it exists with `npx afk-research schedule list`.
- If the user did not name one, list available slugs and ask which schedule should be updated.
- If no Task Prompts exist, say there are no schedules to update and stop.

## Update Flow

1. Run `npx afk-research schedule read <slug>` before asking update questions.
2. Invoke `grill-with-docs`:
   - Run the `/grilling` session it requires.
   - Use `/domain-modeling` as directed to capture stable glossary terms or ADRs only when they genuinely crystallize.
   - Ask one unresolved decision at a time.
3. Ask what should change, why it should change, what must remain unchanged, whether the runner should stay the same, whether the trigger cadence/gap, trigger time, or time zone should change, and whether write permissions or output paths change.
4. Draft the revised Task Prompt body in a temporary file or pass it through stdin when the body changes. Do not place drafts under `.schedule/tasks/`.
5. Run `npx afk-research schedule update <slug>` with the resolved options:

```sh
npx afk-research schedule update <slug> --runner codex --trigger-time 10:30 --timezone Asia/Jakarta --every-days 3 --prompt-file /path/to/draft.md --yes
```

Use the user-resolved cadence when the cadence changes: `--daily`, `--weekly`, or `--every-days N`. Use the user-resolved `--trigger-time HH:MM` and `--timezone Area/City` when the trigger changes. Use `--new-slug <new-slug>` when the resolved change includes a rename.

## Validation

Before reporting completion:

1. Run `npx afk-research schedule read <slug>` using the final slug.
2. Confirm the final slug is lowercase kebab-case.
3. Confirm the runner is `codex` or `claude`.
4. Confirm the trigger cadence, trigger time, and time zone match the user-approved schedule.
5. Confirm the body is specific, bounded, non-interactive, and explicit about write permissions.
6. If a Schedule Runner is live, use `check-schedule-runner-status` to confirm the updated task has the expected next occurrence.
7. Report the updated slug and the command the user can run to test it: `npx afk-research schedule run <slug>`.
