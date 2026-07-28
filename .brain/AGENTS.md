<!-- afk-research:managed v1 -->
# Brain Agent Schema

This file is the operating schema for the `.brain` second brain. Follow it for every interaction that touches this vault. Higher-priority system, developer, and user instructions still take precedence.

## Core Rule

Keep the second brain simple. Inside `.brain`, the only content roots are:

- `raw/` - immutable source material and provenance.
- `wiki/` - all agent-maintained knowledge, indexes, logs, templates, drafts, and outputs.

`AGENTS.md` and `CLAUDE.md` stay at `.brain` root as agent entrypoint files. `CLAUDE.md` must contain only `@AGENTS.md`.

## Start Every Interaction

1. Read `.brain/AGENTS.md`.
2. Read `.brain/wiki/index.md`.
3. Read recent entries in `.brain/wiki/log.md`.
4. Search existing wiki pages with `rg` before creating new pages.
5. Classify the work as setup, ingest, query, lint, maintenance, planning, export, import, or schema.
6. Store only durable notes: evidence, decisions, TODOs, open questions, and concise rationale. Do not store private chain-of-thought.

## Folder Conventions

### `raw/`

Immutable source captures and provenance records.

- Use one folder per source when there are multiple source files.
- Prefix source folders with `YYYY-MM-DD_`, for example `raw/YYYY-MM-DD_example-source/`.
- Put attachments in `raw/assets/` when they are shared across sources.
- Do not edit existing raw captures. Add a correction note or a new version instead.

### `wiki/`

All maintained knowledge and operating files.

- `wiki/index.md` - content map. Read first when navigating the wiki.
- `wiki/log.md` - append-only activity log.
- `wiki/sources/` - source summary pages.
- `wiki/concepts/` - durable ideas and patterns.
- `wiki/entities/` - people, organizations, projects, datasets, places, and named things.
- `wiki/claims/` - evidence-bearing claims worth tracking.
- `wiki/questions/` - research questions and durable answers.
- `wiki/syntheses/` - multi-source analysis and evolving theses.
- `wiki/outputs/` - exportable artifacts and examples.
- `wiki/templates/` - reusable templates and checklists.
- `wiki/inbox/` - unprocessed notes or sources waiting for ingest.
- `wiki/scratch/` - temporary agent work notes.
- `wiki/archive/` - superseded or inactive material retained for provenance.

Do not create new top-level content folders under `.brain`. If a new category is needed, add it under `wiki/`.

## Naming

- Use lowercase kebab-case filenames: `example-topic.md`.
- Prefer stable topic names over session names.
- Rename pages only when it improves long-term navigation, and update backlinks plus `wiki/index.md` in the same pass.

## Page Format

Use YAML frontmatter for wiki pages when practical:

```yaml
---
title: "Page Title"
type: source | concept | entity | claim | question | synthesis | output
status: seed | active | needs-review | superseded
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources:
  - "[[wiki/sources/example-source]]"
tags:
  - tag-name
---
```

Useful sections:

- Summary
- Key Points
- Evidence
- Links
- Conflicts / Updates
- Open Questions
- Next Actions

Do not force every section onto every page. Keep pages clear and maintainable.

## Linking And Evidence

- Use explicit Obsidian wikilinks from the vault root, for example `[[wiki/concepts/example-concept]]`.
- Cite source pages for claims, not just external URLs.
- Link raw provenance when useful, for example `[[raw/YYYY-MM-DD_example-source/source]]`.
- If evidence is weak, mark it as `needs-review` instead of overstating confidence.
- When a new source contradicts an older page, update the affected wiki page and record the conflict in `Conflicts / Updates`.

## Ingest Workflow

Use this workflow when the user gives a source, asks to ingest, or places material in `wiki/inbox/`:

1. Capture or reference the source under `raw/` and keep it immutable.
2. Create or update one source page under `wiki/sources/`.
3. Extract durable concepts, entities, claims, and questions.
4. Search existing wiki pages for overlap before creating new pages.
5. Update relevant concept/entity/claim/synthesis pages under `wiki/`.
6. Add useful cross-links in both directions.
7. Update `wiki/index.md`.
8. Append a log entry to `wiki/log.md` with the exact files created or changed.
9. Complete the Repository Publish Step for the `.brain` files changed by this source ingest.
10. Report the important updates to the user and name unresolved questions.

Prefer one source at a time when judgment, emphasis, or contradiction handling matters.

## Query Workflow

Use this workflow when the user asks a question:

1. Read `wiki/index.md`.
2. Search relevant wiki pages with `rg`.
3. Read the strongest matching pages and their cited sources.
4. Answer with citations to wiki pages and external sources when used.
5. If the answer creates reusable knowledge, file it under `wiki/questions/`, `wiki/syntheses/`, or `wiki/outputs/`.
6. Update `wiki/index.md` and append `wiki/log.md` if the vault changed.
7. If the vault changed, complete the Repository Publish Step for the `.brain` files changed by the query.

## Lint Workflow

Use this workflow when the user asks for a health check or when maintenance is clearly needed:

1. Find orphan pages, duplicate concepts, weakly sourced claims, stale summaries, missing backlinks, and broken links.
2. Check whether newer sources supersede older claims.
3. Suggest or make focused fixes depending on the user's request.
4. Log the lint pass and any edits in `wiki/log.md`.
5. If the lint pass changed the vault, complete the Repository Publish Step for the `.brain` files changed by the lint.

## Import Workflow

Use this workflow when the user provides a Brain Archive or asks to merge another `.brain` vault into the current one:

1. Validate the archive and stage its contents outside `.brain`.
2. Reject unsafe or ambiguous archives before modifying the current vault.
3. Add missing knowledge and semantically merge wiki pages when the merge is clear.
4. Preserve raw collisions, imported schemas, and imported operational files as provenance instead of overwriting active files.
5. Update `wiki/index.md` for created, archived, or materially changed pages.
6. Append one `import` log entry with the archive path, files changed, key result, and follow-ups.
7. Complete the Repository Publish Step for the `.brain` files changed by the import.

## Setup Workflow

Use this workflow when the user asks to initialize, repair, or upgrade the repository-local `.brain` vault:

1. Create missing standard folders and seed files additively.
2. Treat an existing `.brain/AGENTS.md` as authoritative unless the user explicitly approves a schema change.
3. Do not overwrite existing `.brain` content.
4. Ensure generated brain-transfer artifacts under `.outputs/` are ignored by Git.
5. Append a `setup` log entry when setup changes the vault.
6. Complete the Repository Publish Step for the `.brain` files changed by setup.

## Index Contract

`wiki/index.md` is content-oriented. It must list important pages by category with a one-line description. Update it whenever pages are created, renamed, archived, or materially changed.

At minimum, keep these sections:

- Start Here
- Folder Conventions
- Sources
- Concepts
- Entities
- Claims
- Questions
- Syntheses
- Outputs
- Open Threads

## Log Contract

`wiki/log.md` is chronological and append-only. Each durable event uses this heading:

```markdown
## [YYYY-MM-DD] type | Title
```

Allowed `type` values: `setup`, `ingest`, `query`, `lint`, `maintenance`, `export`, `import`, `schema`.

Each entry should include:

- Trigger
- Files changed
- Key result
- Follow-ups

## Repository Publish Step

Every brain operation that creates, modifies, deletes, or renames files under `.brain` must commit and push those `.brain` changes to the repository remote before the operation is considered complete.

1. Run `git status --short` and identify only the `.brain` files changed by the current operation.
2. Stage only those `.brain` files. Do not stage unrelated user changes, product/source edits, or files from a different task unless the user explicitly asked for them.
3. Commit with a concise message in the form `brain: <operation summary>`, for example `brain: ingest lodging notes`, `brain: answer pricing question`, or `brain: lint wiki`.
4. Push the current branch to its upstream. If no upstream is configured, push with `git push -u origin HEAD` when `origin` exists.
5. Report the branch and commit hash. If there are no `.brain` changes, skip the commit/push and say that no repository publish was needed.
6. If commit or push fails because of authentication, missing remotes, network errors, or remote rejection, keep the local working tree safe and report the exact blocker plus the command the user should rerun.

## Editing Rules

- Keep raw captures immutable.
- Keep all second-brain work inside `.brain`.
- Keep content under only `raw/` and `wiki/`.
- Avoid duplicate pages; merge or cross-link instead.
- Prefer concise pages that can be maintained over long dumps.
- Do not hide uncertainty. Mark TODOs and open questions explicitly.
- Schema changes go in `.brain/AGENTS.md`, and the change must be logged in `wiki/log.md`.

## User Collaboration

The user is the editor-in-chief. Ask for direction when a source can be interpreted in materially different ways. Otherwise, proceed pragmatically, file durable knowledge, and keep the final response focused on what changed, what was learned, and what remains open.
