---
name: design-workspace
description: Refocus AI Agent onto a project's `.design` Design Workspace instead of treating the repository root as the primary workspace. Use when the user asks to focus, switch, enter, or work from `.design`; when a task should follow Design Workspace or Design System guidance; or before user-facing UI/design work where `.design/AGENTS.md`, `.brain/AGENTS.md`, and design-system files should shape the agent's behavior.
disable-model-invocation: true
---

# Design Workspace

## Core Rule

Use `.design` as the default working scope for design-focused tasks. Preserve higher-priority repo instructions, but search, read, and edit Design Workspace files before expanding to repository-level files.

## Startup

1. Read the root `AGENTS.md` if present.
2. If `.brain/AGENTS.md` exists, read it before using `.brain`; follow it for second-brain queries, notes, logs, and durable knowledge.
3. Locate the nearest `.design` directory from the current workspace or repository root.
4. If `.design/AGENTS.md` exists, read it and treat it as the operating guide for Design Workspace contents.
5. Inspect `.design/design-system/` for available Design Systems before making user-facing UI or visual decisions.

If `.design` does not exist, say that the project has no initialized Design Workspace. Do not create one unless the user explicitly asks to initialize or add a Design System.

## Working Pattern

- Treat `.design` as the task workspace: run targeted searches there first, keep design notes and design artifacts there, and reference paths relative to `.design` when useful.
- Read a named Design System's `README.md` and `DESIGN.md` before implementation.
- If multiple Design Systems exist and the user has not named one, ask which one to use.
- If `design-system/` is empty, ask which Design System to create or use. Do not invent a Design System name, visual direction, tokens, or style language.
- Treat Design System files as user-authored product decisions. Do not overwrite them unless the user explicitly asks.
- Use repository-level files only when needed for constraints, implementation, tests, or commands that must run from the project root.
- Keep source code changes in normal source paths when the user asks for implementation. The Design Workspace is the design authority, not a replacement for product code locations.

## Creation Boundary

When the user explicitly asks to create or add a Design System:

1. Prefer the project's own command, usually `afk-research design add "<Design System Name>"`, when available.
2. Preserve the user-provided Design System Name and derive only storage slugs when the project command or local convention requires it.
3. Create neutral placeholders only. Leave product-specific visual choices, tokens, and style language for the user.
4. Avoid modifying root `AGENTS.md`, `.brain/AGENTS.md`, or unrelated Design Systems unless the user asks.

## Completion

Report which `.design` files were read or changed, whether `.brain` was consulted or updated, and any cases where work had to expand beyond the Design Workspace.
