---
name: start-schedule-runner
description: Start the project-local Schedule Runner after checking Schedule Workspace tasks and guiding Codex and Claude Code authentication when needed.
disable-model-invocation: true
---

# Start Schedule Runner

## Startup

1. Follow repository instructions first.
2. Invoke `schedule-workspace` first by reading and applying `.agents/skills/schedule-workspace/SKILL.md` when present.
3. Follow its startup sequence, including reading `.schedule/AGENTS.md` and inspecting `.schedule/tasks/`.
4. Run `npx afk-research schedule status --json`. If the runner is already live, report its status and stop without running readiness probes.
5. Run `npx afk-research schedule list` and stop if there are no Task Prompts. Every Task Prompt must have a valid runner, non-empty prompt, and complete trigger metadata before startup.

## Start Flow

1. Explain that startup makes fresh, concurrent, minimal model calls through both Codex and Claude Code in isolated temporary directories. The CLI blocks startup unless both agent CLIs are installed, authenticated, and usable.
2. Ask for explicit confirmation before running the probes and starting the runner.
3. Run `npx afk-research schedule start` from the project root. Sleep-resilient Host Wake support is mandatory. On macOS, if the CLI reports that the Host Wake Helper is missing or unusable, ask for approval and run `npx afk-research schedule wake-helper install` to install or upgrade it before retrying startup.
4. If the CLI reports that Codex is missing, provide installation guidance. If it reports a Codex authentication failure, offer to run `codex login` interactively.
5. If the CLI reports that Claude Code is missing, provide installation guidance. If it reports a Claude Code authentication failure, offer to run `claude auth login` interactively.
6. After approved authentication flows finish, retry `npx afk-research schedule start` once. Do not loop. If readiness still fails, report both results and the relevant manual login commands.
7. On success, run `npx afk-research schedule status --json` and report runner state, PID, mode, start time, heartbeat, Host Wake Entry state, next wake, and each task's next occurrence.

Never request, read, copy, or store credentials. Authentication belongs to the agent CLI's interactive login flow.
