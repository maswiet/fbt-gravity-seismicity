---
name: lint
description: Audit and maintain the repository-local `.brain` second brain by invoking `brain-workspace` and following the live `.brain/AGENTS.md` Lint Workflow. Use when the user asks to lint, audit, health check, clean up, find broken links, find orphan pages, deduplicate concepts, check weak sourcing, detect stale summaries, or identify maintenance issues in `.brain` or the wiki.
disable-model-invocation: true
---

# Lint

## Core Rule

Use the repository-local `.brain` vault as the only work area for second-brain linting. Check the maintained wiki for structural, sourcing, freshness, and link-health problems; suggest or make focused fixes according to the user's request; log every lint pass and every edit.

## Startup

1. Invoke the `brain-workspace` behavior first:
   - If `.agents/skills/brain-workspace/SKILL.md` exists in the repo, read it and apply it.
   - Otherwise, apply any available `$brain-workspace` skill instructions.
   - Do this yourself; do not ask the user to separately invoke `brain-workspace`.
2. Read workspace `AGENTS.md` files that apply to the current repo. If `.brain/AGENTS.md` exists, read it as the authoritative operating schema for `.brain`.
3. Read `.brain/wiki/index.md`.
4. Read recent entries in `.brain/wiki/log.md` to understand recent changes and unresolved follow-ups.
5. Classify the task as `lint` unless the user explicitly asks to ingest, query, export, or change the schema.

## Lint Operation

Follow the live `.brain/AGENTS.md` Lint Workflow exactly. At minimum:

1. Find orphan pages, duplicate concepts, weakly sourced claims, stale summaries, missing backlinks, and broken links.
2. Check whether newer sources supersede older claims.
3. Suggest or make focused fixes depending on the user's request.
4. Log the lint pass and any edits in `.brain/wiki/log.md`.
5. If the lint pass changed `.brain`, commit and push only the `.brain` files changed by this lint.

## Audit Checklist

- Verify `.brain` keeps only the allowed root content folders from `.brain/AGENTS.md`.
- Check that important pages appear in `.brain/wiki/index.md` under the right category.
- Check wikilinks from the vault root and report unresolved or renamed targets.
- Check source, concept, entity, claim, question, synthesis, and output pages for missing useful backlinks.
- Check claims and summaries against cited source pages and raw provenance when needed.
- Search for near-duplicate pages before recommending merges or renames.
- Look for stale pages by comparing `updated` metadata, log entries, and newer source pages.
- Preserve uncertainty; mark weak evidence or ambiguous cleanup as follow-up instead of over-editing.

## Fix Rules

- If the user asks for a report only, do not edit wiki content except for the required lint log entry if the live schema requires logging the pass.
- If the user asks to clean up or fix issues, make small, focused edits inside `.brain/wiki/`.
- Do not edit existing raw captures. Add notes, corrections, or new maintained wiki pages instead.
- Update `.brain/wiki/index.md` whenever pages are created, renamed, archived, materially changed, or newly important.
- Append a `lint` entry to `.brain/wiki/log.md` with the trigger, files changed, key result, and follow-ups.
- Do not modify product/source files or issue trackers during lint unless the user separately asks for that work.

## Repository Publish Rules

- After a lint pass that changes `.brain`, run `git status --short`, stage only this lint's `.brain` changes, commit with `brain: lint <focus summary>`, and push the current branch to its upstream.
- If no upstream is configured and `origin` exists, use `git push -u origin HEAD`.
- Do not stage unrelated user changes, non-brain files, or `.brain` files from another task unless the user explicitly asked for them.
- If the lint only reports findings without changing `.brain`, skip the commit/push and say no repository publish was needed.
- If commit or push fails, keep the local changes intact and report the exact blocker and rerun command.

## Report Rules

- Lead with the highest-impact findings or fixes.
- Include exact `.brain` files inspected or changed.
- Separate fixed issues from remaining recommendations.
- Name unresolved questions, risky merges, or cases that need the user's editorial judgment.
- Do not store private chain-of-thought. Store evidence, decisions, TODOs, open questions, and concise rationale only.
