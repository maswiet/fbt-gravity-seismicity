---
name: export-brain
description: Export the repository-local `.brain` second brain as a portable zip archive under `.outputs/`. Use when the user asks to preserve, back up, package, transfer, save, or export `.brain` knowledge without changing the current vault.
disable-model-invocation: true
---

# Export Brain

## Core Rule

Create a read-only Brain Export. Package the current `.brain` directory into a zip whose archive root contains one `.brain/` folder, place generated artifacts under `.outputs/`, and leave `.brain` unchanged.

## Workflow

1. Locate the repository root and verify `.brain` exists.
2. Read `.brain/AGENTS.md` when present so the export respects the local Second Brain schema.
3. Run the helper script from the repository root:

```bash
python3 .agents/skills/export-brain/scripts/export_brain.py
```

4. Report the generated zip, manifest, checksum, file count, and any skipped files.

## Archive Contract

- Store files in the zip under a top-level `.brain/` folder.
- Include only `.brain` contents.
- Exclude Git metadata, OS noise, Python caches, temp files, and generated export/import artifacts.
- Write outputs under `.outputs/`, which should be ignored by Git.
- Do not append `.brain/wiki/log.md`.
- Do not commit or push after export unless the user separately asks for Git operations on non-output files.

## Helper Script

`scripts/export_brain.py` creates:

- `.outputs/brain-export-<timestamp>.zip`
- `.outputs/brain-export-<timestamp>.manifest.json`
- `.outputs/brain-export-<timestamp>.zip.sha256`

Use `--output-dir`, `--brain-dir`, or `--name` only when the user asks for a non-default location or filename.
