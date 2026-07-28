---
name: query
description: Answer user questions from the repository-local `.brain` second brain by invoking `brain-workspace` and following the live `.brain/AGENTS.md` Query Workflow. Use when the user asks to query, search, look up, synthesize, retrieve, summarize, or answer from `.brain`, the wiki, the second brain, saved sources, or previously ingested material.
disable-model-invocation: true
---

# Query

## Core Rule

Use the repository-local `.brain` vault as the source of truth for answers about saved or ingested knowledge. Read before answering, cite the wiki pages and external sources used, and only modify `.brain` when the answer creates reusable durable knowledge.

## Startup

1. Invoke the `brain-workspace` behavior first:
   - If `.agents/skills/brain-workspace/SKILL.md` exists in the repo, read it and apply it.
   - Otherwise, apply any available `$brain-workspace` skill instructions.
   - Do this yourself; do not ask the user to separately invoke `brain-workspace`.
2. Read workspace `AGENTS.md` files that apply to the current repo. If `.brain/AGENTS.md` exists, read it as the authoritative operating schema for `.brain`.
3. Read `.brain/wiki/index.md`.
4. Read recent entries in `.brain/wiki/log.md` when they may affect freshness, conflicts, or recently changed pages.
5. Classify the task as `query` unless the user explicitly asks to ingest, lint, export, or change the schema.

## Query Operation

Follow the live `.brain/AGENTS.md` Query Workflow exactly. At minimum:

1. Read `.brain/wiki/index.md`.
2. Search relevant wiki pages with `rg`.
3. Read the strongest matching pages and their cited source pages or raw provenance when needed.
4. Answer with citations to wiki pages and external sources when used.
5. If the answer creates reusable knowledge, file it under `.brain/wiki/questions/`, `.brain/wiki/syntheses/`, or `.brain/wiki/outputs/`.
6. Update `.brain/wiki/index.md` and append `.brain/wiki/log.md` if the vault changed.
7. If the vault changed, commit and push only the `.brain` files changed by this query.

## Answer Rules

- Prefer answers grounded in `.brain/wiki/` pages over memory.
- Say when `.brain` does not contain enough evidence to answer.
- Distinguish sourced facts, synthesis, and inference.
- Preserve uncertainty and mention conflicts or stale information when found.
- Keep citations precise enough for the user to inspect the source pages.
- Do not browse the web unless the user asks for fresh external verification or the answer cannot be responsibly completed from `.brain`.
- Do not modify product/source files, raw captures, or issue trackers during a query unless the user separately asks for that work.

## Writeback Rules

- Write to `.brain` only when the query produces durable knowledge worth reusing, such as a stable answer, synthesis, output artifact, open question, or correction.
- Keep all query-created artifacts under `.brain/wiki/questions/`, `.brain/wiki/syntheses/`, `.brain/wiki/outputs/`, or another folder allowed by `.brain/AGENTS.md`.
- Use concise Markdown with YAML frontmatter when practical.
- Update `.brain/wiki/index.md` and append a `query` entry to `.brain/wiki/log.md` for every vault change.
- Do not store private chain-of-thought. Store evidence, decisions, TODOs, open questions, and concise rationale only.

## Repository Publish Rules

- After a query that changes `.brain`, run `git status --short`, stage only this query's `.brain` changes, commit with `brain: answer <topic summary>`, and push the current branch to its upstream.
- If no upstream is configured and `origin` exists, use `git push -u origin HEAD`.
- Do not stage unrelated user changes, non-brain files, or `.brain` files from another task unless the user explicitly asked for them.
- If the query only reads from `.brain`, skip the commit/push and say no repository publish was needed.
- If commit or push fails, keep the local changes intact and report the exact blocker and rerun command.
