---
name: create-schedule
description: Create a Scheduled Job Task Prompt under `.schedule/tasks/` by invoking schedule-workspace first, asking what schedule should be created, and using grill-with-docs to sharpen the unattended task. Use when the user asks to create, add, draft, or define a new schedule, Scheduled Job, recurring agent task, or schedule Task Prompt.
disable-model-invocation: true
---

# Create Schedule

## Core Rule

Create a Task Prompt through the AFK Research CLI. Do not write `.schedule/tasks/*.md` directly unless the CLI is unavailable and the user explicitly approves a fallback.

## Startup

1. Follow repo instructions first. If root `AGENTS.md` requires `/query`, ask `.brain` for relevant schedule, domain, and safety context before planning or editing.
2. Invoke `schedule-workspace` first:
   - Read and apply `.agents/skills/schedule-workspace/SKILL.md` when it exists.
   - Follow its startup sequence, including root `AGENTS.md`, `.brain/AGENTS.md` when present, `.schedule/AGENTS.md`, and `.schedule/tasks/` inspection.
3. If `.schedule` does not exist, say the project has no initialized Schedule Workspace and stop unless the user explicitly asks to initialize scheduled jobs.
4. Run `npx afk-research schedule list` to inspect existing Task Prompt slugs before choosing a new slug.

## Creation Flow

1. If the user did not say what to create, ask what Scheduled Job or Task Prompt they want. Provide one recommended low-risk, report-only option when project context suggests one.
2. Derive a lowercase kebab-case slug from the chosen task name. If the slug already exists, ask whether to update the existing schedule or choose a different slug.
3. Invoke `grill-with-docs`:
   - Run the `/grilling` session it requires.
   - Use `/domain-modeling` as directed to capture stable glossary terms or ADRs only when they genuinely crystallize.
   - Ask one unresolved decision at a time.
4. Resolve, at minimum, the Task Prompt purpose, runner (`codex` or `claude`), trigger cadence or gap (`daily`, `weekly`, or every N days), trigger time, time zone, whether writes are allowed, exact allowed paths for writes, expected output/log location, and any schedule cadence guidance the user wants documented.
5. Draft the Task Prompt body in a temporary file or pass it through stdin. Do not place the draft under `.schedule/tasks/`.
6. Run the CLI to create the Task Prompt:

```sh
npx afk-research schedule create <slug> --runner codex --trigger-time 09:00 --timezone Asia/Jakarta --weekly --prompt-file /path/to/draft.md --yes
```

Use the user-resolved cadence: `--daily`, `--weekly`, or `--every-days N`. Use the user-resolved `--trigger-time HH:MM` and `--timezone Area/City`; these values become portable Task Prompt metadata. Use `--runner claude` when the resolved runner is Claude Code. Use `--stdin` or `--prompt` instead of `--prompt-file` only when that is safer for the current environment.

## Validation

Before reporting completion:

1. Run `npx afk-research schedule read <slug>` and inspect the CLI output.
2. Confirm the slug is lowercase kebab-case.
3. Confirm the runner is `codex` or `claude`.
4. Confirm the trigger cadence, trigger time, and time zone match the user-approved schedule.
5. Confirm the body is specific, bounded, non-interactive, and explicit about write permissions.
6. If a Schedule Runner is live, use `check-schedule-runner-status` to confirm the task has a computed next occurrence.
7. Report the created slug and the command the user can run to test it: `npx afk-research schedule run <slug>`.
