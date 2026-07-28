<!-- afk-research:managed v1 -->
# Schedule Workspace

## Agent Instructions

Scheduled Jobs run unattended. Treat every Task Prompt as a low-risk automation contract, not a general implementation request.

Keep Task Prompts in `tasks/` and name them with lowercase kebab-case slugs such as `weekly-brain-lint.md`. The active schedule set is the files that exist under `tasks/`: if a Task Prompt exists and has complete trigger metadata, the Schedule Runner can run it; if it is deleted, it no longer runs.

Use the AFK Research CLI for Task Prompt create, read, update, delete, and runner lifecycle operations. Agents should not hand-edit files under `tasks/` unless the CLI is unavailable and the project owner explicitly approves a fallback. Do not create or edit `.schedule/schedule.json`; that legacy host scheduler manifest is removed automatically by Schedule Runner commands.

```sh
npx afk-research schedule list
npx afk-research schedule read <task-slug>
npx afk-research schedule create <task-slug> --runner codex --trigger-time 09:00 --timezone Asia/Jakarta --weekly --prompt-file /path/to/draft.md --yes
npx afk-research schedule update <task-slug> --trigger-time 10:30 --timezone Asia/Jakarta --every-days 3 --prompt-file /path/to/draft.md --yes
npx afk-research schedule delete <task-slug> --yes
npx afk-research schedule status
npx afk-research schedule work
npx afk-research schedule start
npx afk-research schedule stop
npx afk-research schedule wake-helper install # macOS one-time setup only
npx afk-research schedule wake-helper uninstall # macOS cleanup after every runner is stopped
```

Each Task Prompt must start with YAML frontmatter declaring the runner. Task Prompts may also include `trigger_time`, `timezone`, and `trigger_interval_days` metadata written by the CLI:

```markdown
---
runner: codex
trigger_time: "09:00"
timezone: "Asia/Jakarta"
trigger_interval_days: 7
---

Summarize the current project state and write no files.
```

Task Prompt trigger metadata is the portable schedule definition. There is no separate per-host schedule configuration file.

Allowed runners are:

- `codex` - runs with `codex exec --dangerously-bypass-approvals-and-sandbox`.
- `claude` - runs with `claude -p --dangerously-skip-permissions`.

Prefer trivial, report-only jobs. Do not schedule destructive work, package installs, broad refactors, credential access, deployment, repository reset, or unattended commits unless the project owner explicitly accepts that risk for a specific task.

## Task Prompt Rules

- Keep prompts specific and bounded.
- State whether the task may write files. If it may write files, name exact paths.
- Include the expected output location when the scheduler redirects logs.
- Do not include secrets in prompts, scheduler files, environment variables, command lines, or logs.
- Do not rely on interactive questions or approvals; Scheduled Jobs must be able to finish unattended.
- Do not add occurrence limits such as `max_runs`; recurring Scheduled Jobs are controlled by keeping, updating, or deleting the Task Prompt.

## Schedule Runner

Use `schedule work` for a foreground-only runner while debugging. It does not provide sleep-resilient scheduling:

```sh
npx afk-research schedule work
```

Foreground and detached startup require every Task Prompt to be runnable. Before startup, the CLI makes fresh concurrent minimal model calls through both Codex and Claude Code in isolated temporary directories. Startup is blocked unless both CLIs are installed, authenticated, and usable. These readiness results are not cached. A detached worker spawned internally by `schedule start` does not repeat the probes.

Use `schedule start` for a sleep-resilient detached Schedule Runner. Startup succeeds only after a wake-capable Host Wake Entry is verified:

```sh
npx afk-research schedule start
```

On macOS, install the narrowly privileged Host Wake Helper before the first start or run the same command to upgrade it:

```sh
npx afk-research schedule wake-helper install
```

After every Schedule Runner has been stopped and its Host Wake Entry removed, uninstall the helper and sudoers policy with `npx afk-research schedule wake-helper uninstall`.

Inspect operational state with:

```sh
npx afk-research schedule status
```

Stop the runner and confirm removal of the project-level Host Wake Entry with:

```sh
npx afk-research schedule stop
```

`schedule create`, `schedule update`, and `schedule delete` notify a live Schedule Runner and recalculate the next Host Wake Entry, but they do not run jobs immediately. When the runner ticks or wakes at a due time, it runs all Scheduled Jobs due at or before that time, then recalculates the next Host Wake Entry.

Schedule Runner state, per-task occurrence bookkeeping, run history, logs, and Host Wake Entry state live under `.outputs/schedule/`.

## Manual Run

Run one Task Prompt manually from the project root:

```sh
npx afk-research schedule run <task-slug>
```

From another working directory:

```sh
npx afk-research schedule run <task-slug> --path /absolute/path/to/project
```

A manual run first makes one isolated minimal model call through the Task Prompt's selected runner. The actual Task Prompt runs only after that fresh readiness probe succeeds.

Legacy per-task Host Schedule Entries and `.schedule/schedule.json` are cleaned up automatically when `schedule work` or `schedule start` activates the project-local Schedule Runner. There are no public install or audit commands for the legacy integration.
