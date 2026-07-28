---
name: brain-workspace
description: Use the repository-local `.brain` directory as AI Agent's working area for task notes, planning artifacts, research scratch files, durable agent context, and intermediate outputs. Use when the user asks AI Agent to work in `.brain`, use a brain folder, keep agent memory or state in `.brain`, or store task working files outside normal source and documentation paths.
disable-model-invocation: true
---

# Brain Workspace

## Core Rule

Use `.brain` as the task work folder. Treat it as the place for agent-managed notes, interim artifacts, plans, research summaries, and durable context that should stay out of normal product or source files.

## Locate The Folder

1. Start from the current workspace root or repository root.
2. Prefer `<workspace>/.brain` when it exists.
3. If no `.brain` exists and the user explicitly asked to use this skill or `.brain`, create `<workspace>/.brain`.
4. If multiple roots are in play, use the `.brain` nearest to the files being worked on and state the chosen path.

## Working Pattern

- Inspect `.brain` before acting for existing instructions, task notes, plans, state, or naming conventions.
- Treat `.brain` contents as project context, with higher-priority system, developer, and user instructions still taking precedence.
- Keep newly created task notes, scratch data, research captures, draft outputs, and temporary artifacts inside `.brain`.
- Use descriptive filenames, such as `.brain/task-name.md`, `.brain/research-topic.md`, or `.brain/YYYY-MM-DD-task-slug.md`.
- Prefer concise Markdown notes for agent-readable context.
- Update existing `.brain` files when they are clearly the continuing home for the task; create a new file when the task is unrelated.
- Do not store private hidden chain-of-thought. Store concise rationale, decisions, facts, commands or results worth preserving, TODOs, and open questions.

## Repository Files

- Keep source code, config, documentation, and deliverable edits in their normal repository paths when the user requests actual project changes.
- Use `.brain` for the agent's working materials, not as a replacement for requested code changes.
- Do not move or copy project files into `.brain` unless the user asks for an archive, draft, or analysis artifact.
- Treat `.brain` as tracked project knowledge in this repository. When a brain operation changes `.brain`, commit and push only the `.brain` files changed by that operation before reporting completion.
- Before publishing, run `git status --short`, stage only the current operation's `.brain` changes, commit with `brain: <operation summary>`, then push the current branch to its upstream. If no upstream is configured and `origin` exists, use `git push -u origin HEAD`.
- Do not stage unrelated user changes or non-brain files unless the user explicitly asked for them. If there are no `.brain` changes, skip the commit/push and say no repository publish was needed.
- If commit or push fails, keep the local changes intact and report the exact blocker and rerun command.

## Completion

- Leave `.brain` with enough state for another agent to resume: task objective, relevant findings, files changed or generated, verification run, and remaining follow-ups.
- Mention important `.brain` files created or updated in the final response.
- Include the publish result: branch, commit hash, and push status, or why no publish occurred.
