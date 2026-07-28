---
name: stop-schedule-runner
description: Stop the project-local Schedule Runner and clean its Host Wake Entry or stale operational state after confirmation.
disable-model-invocation: true
---

# Stop Schedule Runner

## Flow

1. Follow repository instructions first.
2. Invoke `schedule-workspace` first by reading and applying `.agents/skills/schedule-workspace/SKILL.md` when present.
3. Follow its startup sequence, including reading `.schedule/AGENTS.md` and inspecting `.schedule/tasks/`.
4. Run `npx afk-research schedule status --json`.
5. Treat `wake.installed=false` as a retained diagnostic record, not an installed Host Wake Entry. If the runner process, installed Host Wake Entry, and stale runner state are all absent, report that the runner is already fully stopped and make no changes. Retain any `installed=false` diagnostic so status continues to show the failed-start error and remediation; do not run `schedule stop` merely to clear it.
6. Otherwise, show the current runner and wake state and ask for explicit confirmation. Explain that stopping prevents future scheduling and removes runner-owned wake or stale state, while already-started Codex or Claude Code child processes may finish.
7. After confirmation, run `npx afk-research schedule stop`.
8. Run `npx afk-research schedule status --json` again and report the final state and any cleanup warnings.
