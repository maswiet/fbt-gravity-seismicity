#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def _add_local_lib_to_path() -> None:
    for parent in Path(__file__).resolve().parents:
        if parent.name in {".agents", ".claude"}:
            candidate = parent / "lib"
            if candidate.is_dir():
                sys.path.insert(0, str(candidate))
                return

    for parent in Path(__file__).resolve().parents:
        candidate = parent / ".agents" / "lib"
        if candidate.is_dir():
            sys.path.insert(0, str(candidate))
            return


_add_local_lib_to_path()

from brain_transfer_paths import DEFAULT_OUTPUT_IGNORE_RULE  # noqa: E402


WIKI_DIRS = [
    "sources",
    "concepts",
    "entities",
    "claims",
    "questions",
    "syntheses",
    "outputs",
    "templates",
    "inbox",
    "scratch",
    "archive",
]


AGENTS_TEMPLATE = """# Brain Agent Schema

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
5. Classify the work as ingest, query, lint, maintenance, planning, export, import, setup, or schema.
6. Store only durable notes: evidence, decisions, TODOs, open questions, and concise rationale. Do not store private chain-of-thought.

## Folder Conventions

- `raw/` - Immutable source captures and provenance records.
- `wiki/index.md` - Content map.
- `wiki/log.md` - Append-only activity log.
- `wiki/sources/` - Source summary pages.
- `wiki/concepts/` - Durable ideas and patterns.
- `wiki/entities/` - People, organizations, projects, datasets, places, and named things.
- `wiki/claims/` - Evidence-bearing claims worth tracking.
- `wiki/questions/` - Research questions and durable answers.
- `wiki/syntheses/` - Multi-source analysis and evolving theses.
- `wiki/outputs/` - Exportable artifacts and examples.
- `wiki/templates/` - Reusable templates and checklists.
- `wiki/inbox/` - Unprocessed material waiting for ingest.
- `wiki/scratch/` - Temporary agent work notes.
- `wiki/archive/` - Superseded or inactive material retained for provenance.

Do not create new top-level content folders under `.brain`.

## Repository Publish Step

Every brain operation that creates, modifies, deletes, or renames files under `.brain` must commit and push those `.brain` changes to the repository remote before the operation is considered complete.

1. Run `git status --short` and identify only the `.brain` files changed by the current operation.
2. Stage only those `.brain` files.
3. Commit with a concise `brain: <operation summary>` message.
4. Push the current branch to its upstream. If no upstream is configured and `origin` exists, use `git push -u origin HEAD`.
5. Report the branch and commit hash, or explain why no publish was needed.

## Editing Rules

- Keep raw captures immutable.
- Keep all second-brain work inside `.brain`.
- Keep content under only `raw/` and `wiki/`.
- Avoid duplicate pages; merge or cross-link instead.
- Prefer concise pages that can be maintained over long dumps.
- Do not hide uncertainty. Mark TODOs and open questions explicitly.
"""

INDEX_TEMPLATE = """# Index

This is the content map for the `.brain` second brain. Read this file before answering from or editing the wiki. Update it on every ingest and every durable query that changes the vault.

Last updated: {today} setup

## Start Here

- [[AGENTS|AGENTS.md]] - Operating schema for the LLM wiki agent.
- [[CLAUDE|CLAUDE.md]] - Claude-compatible pointer to the schema.
- [[wiki/log|log.md]] - Append-only chronological activity log.

## Folder Conventions

- `raw/` - Immutable source captures and provenance records.
- `wiki/` - All maintained knowledge and operating files.

## Sources

- No source pages currently.

## Concepts

- No concept pages currently.

## Entities

- No entity pages currently.

## Claims

- No standalone claim pages yet.

## Questions

- No durable question pages yet.

## Syntheses

- No synthesis pages yet.

## Outputs

- No output pages currently.

## Templates

- [[wiki/templates/source-page]] - Template for source summary pages.
- [[wiki/templates/concept-page]] - Template for concept pages.
- [[wiki/templates/entity-page]] - Template for entity pages.
- [[wiki/templates/ingest-checklist]] - Checklist for future ingest work.

## Open Threads

- Keep all second-brain work inside `.brain`, with content organized under only `raw/` and `wiki/`.
"""

LOG_TEMPLATE = """# Log

Append-only chronological record for the `.brain` second brain. Use headings in this format:

```markdown
## [YYYY-MM-DD] type | Title
```

Allowed types: `setup`, `ingest`, `query`, `lint`, `maintenance`, `export`, `import`, `schema`.

Initial setup baseline retained before dated activity entries.
"""

SOURCE_TEMPLATE = """---
title: "Source Title"
type: source
status: seed
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
tags: []
---

## Summary

## Key Points

## Links
"""

CONCEPT_TEMPLATE = """---
title: "Concept Name"
type: concept
status: seed
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
tags: []
---

## Summary

## Key Points

## Evidence

## Links
"""

ENTITY_TEMPLATE = """---
title: "Entity Name"
type: entity
status: seed
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: []
tags: []
---

## Summary

## Known Facts

## Links
"""

INGEST_CHECKLIST = """# Ingest Checklist

- Capture or reference the source under `.brain/raw/`.
- Create or update a source page under `.brain/wiki/sources/`.
- Search existing wiki pages before creating new concept, entity, claim, question, or synthesis pages.
- Add useful backlinks and citations.
- Update `.brain/wiki/index.md`.
- Append `.brain/wiki/log.md`.
- Commit and push only the `.brain` files changed by this ingest.
"""


SEED_FILES = {
    "AGENTS.md": AGENTS_TEMPLATE,
    "CLAUDE.md": "@AGENTS.md\n",
    "wiki/index.md": INDEX_TEMPLATE,
    "wiki/log.md": LOG_TEMPLATE,
    "wiki/templates/source-page.md": SOURCE_TEMPLATE,
    "wiki/templates/concept-page.md": CONCEPT_TEMPLATE,
    "wiki/templates/entity-page.md": ENTITY_TEMPLATE,
    "wiki/templates/ingest-checklist.md": INGEST_CHECKLIST,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize or repair a repository-local .brain vault.")
    parser.add_argument("--repo-root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--brain-dir", default=".brain", help="Brain directory relative to repo root.")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files.")
    return parser.parse_args()


def write_if_missing(path: Path, content: str, changes: list[str], dry_run: bool) -> None:
    if path.exists():
        return
    changes.append(str(path))
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_dir(path: Path, changes: list[str], dry_run: bool) -> None:
    if path.exists():
        return
    changes.append(str(path) + "/")
    if not dry_run:
        path.mkdir(parents=True, exist_ok=True)


def append_setup_log(log_path: Path, changed_paths: list[str], dry_run: bool) -> None:
    if not changed_paths:
        return
    today = date.today().isoformat()
    entry = (
        f"\n## [{today}] setup | Setup brain vault\n\n"
        "- Trigger: `setup-brain` initialized or repaired the repository-local Second Brain.\n"
        "- Files changed: " + ", ".join(f"`{path}`" for path in changed_paths) + ".\n"
        "- Key result: Missing standard `.brain` folders or seed files were created without overwriting existing content.\n"
        "- Follow-ups: Continue using the live `.brain/AGENTS.md` schema for future brain operations.\n"
    )
    if dry_run:
        return
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def ensure_gitignore_output(repo_root: Path, repo_changes: list[str], dry_run: bool) -> None:
    gitignore_path = repo_root / ".gitignore"
    normalized_rule = DEFAULT_OUTPUT_IGNORE_RULE.rstrip("/")
    if gitignore_path.exists():
        lines = gitignore_path.read_text(encoding="utf-8").splitlines()
        if any(line.strip().rstrip("/") == normalized_rule for line in lines):
            return
        content = gitignore_path.read_text(encoding="utf-8")
        insertion = (
            f"\n{DEFAULT_OUTPUT_IGNORE_RULE}\n"
            if content and not content.endswith("\n")
            else f"{DEFAULT_OUTPUT_IGNORE_RULE}\n"
        )
        repo_changes.append(str(gitignore_path))
        if not dry_run:
            with gitignore_path.open("a", encoding="utf-8") as handle:
                handle.write(insertion)
        return

    repo_changes.append(str(gitignore_path))
    if not dry_run:
        gitignore_path.write_text(
            f"# Generated brain-transfer artifacts\n{DEFAULT_OUTPUT_IGNORE_RULE}\n",
            encoding="utf-8",
        )


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    brain_dir = (repo_root / args.brain_dir).resolve()
    today = date.today().isoformat()
    brain_changes: list[str] = []
    repo_changes: list[str] = []

    ensure_dir(brain_dir, brain_changes, args.dry_run)
    ensure_dir(brain_dir / "raw", brain_changes, args.dry_run)
    ensure_dir(brain_dir / "wiki", brain_changes, args.dry_run)
    for wiki_dir in WIKI_DIRS:
        ensure_dir(brain_dir / "wiki" / wiki_dir, brain_changes, args.dry_run)

    for relative_path, template in SEED_FILES.items():
        content = template.format(today=today) if "{today}" in template else template
        write_if_missing(brain_dir / relative_path, content, brain_changes, args.dry_run)

    ensure_gitignore_output(repo_root, repo_changes, args.dry_run)

    log_path = brain_dir / "wiki" / "log.md"
    relative_brain_changes = [
        str(Path(path).resolve().relative_to(repo_root)) if Path(path).is_absolute() else path
        for path in brain_changes
    ]
    if brain_changes and log_path.exists():
        append_setup_log(log_path, relative_brain_changes, args.dry_run)
        if str(log_path) not in brain_changes:
            brain_changes.append(str(log_path))
            relative_brain_changes.append(str(log_path.relative_to(repo_root)))

    relative_repo_changes = [
        str(Path(path).resolve().relative_to(repo_root)) if Path(path).is_absolute() else path
        for path in repo_changes
    ]

    print(json.dumps(
        {
            "brain_dir": str(brain_dir),
            "dry_run": args.dry_run,
            "changed": bool(brain_changes or repo_changes),
            "brain_changed": bool(brain_changes),
            "repo_changed": bool(repo_changes),
            "brain_changes": relative_brain_changes,
            "repo_changes": relative_repo_changes,
        },
        indent=2,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
