<!-- afk-research:managed v1 -->
# AGENTS.md

## Agent skills

### Project knowledge

Before planning, designing, or implementing work, use the `/query` skill to ask the `.brain` knowledge base for relevant fundamentals, domain context, prior decisions, requirements, constraints, and open questions. Use `/query` whenever the agent needs the same project understanding a human contributor would need before acting.

### Design Workspace

Before user-facing UI work, if `.design/` exists, read `.design/AGENTS.md` and follow the selected Design System guidance.

### Schedule Workspace

Before creating or changing Scheduled Jobs, if `.schedule/` exists, read `.schedule/AGENTS.md` and keep Task Prompts under `.schedule/tasks/`.

### Issue tracker

Issues and PRDs are tracked in GitHub Issues for this codebase remote repository; external PRs are not treated as a triage request surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-label triage vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, and `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

This repo uses a single-context domain documentation layout. See `docs/agents/domain.md`.
