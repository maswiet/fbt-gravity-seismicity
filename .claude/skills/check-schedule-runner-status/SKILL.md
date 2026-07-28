---
name: check-schedule-runner-status
description: Read and summarize the project-local Schedule Runner's operational status without starting jobs or probing agent authentication.
disable-model-invocation: true
---

# Check Schedule Runner Status

## Flow

1. Follow repository instructions first.
2. Invoke `schedule-workspace` first by reading and applying `.agents/skills/schedule-workspace/SKILL.md` when present.
3. Follow its startup sequence, including reading `.schedule/AGENTS.md` and inspecting `.schedule/tasks/`.
4. Run `npx afk-research schedule status --json` as the authoritative read.
5. Report the runner state (`running`, `stopped`, or `stale`), PID, mode, start time, heartbeat, Host Wake Entry state, next wake time, and all warnings.
6. For every Task Prompt, report its selected runner, trigger, last scheduled occurrence, and next scheduled occurrence.

This skill is read-only. Do not run Runner Readiness Verification, start or stop the runner, run a Task Prompt, or launch authentication flows.
