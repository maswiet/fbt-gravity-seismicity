---
name: archive-implementation
description: Move implementation work out of an AFK Research setup into a named `.archive/archive-name/` folder while preserving setup baseline files, `.brain`, and other dot-prefixed project files. Use when the user wants to reset a project back toward its initial `afk-research init` setup state, archive messy implementation work, or clear non-setup source/docs/assets without losing them.
disable-model-invocation: true
---

# Archive Implementation

## Core Rule

Move implementation work into `.archive/<archive-name>/`; do not copy it. Always preserve top-level dot-prefixed paths such as `.brain`, `.agents`, `.claude`, `.git`, `.gitignore`, and `.archive`.

Use the AFK manifest at `.agents/afk-research-manifest.json` as the setup baseline when it exists. If the manifest is missing, stop after explaining the risk and ask the user before using the fallback candidate list.

## Workflow

1. Ask for the archive name if the user did not provide one.
2. Run the helper script in dry-run mode from the project root:

   ```sh
   python3 .agents/skills/archive-implementation/scripts/archive_implementation.py --archive-name "<archive name>"
   ```

3. Show the user the normalized archive path and the planned moves.
4. Ask for explicit confirmation before applying the plan.
5. Apply the move with the same archive name:

   ```sh
   python3 .agents/skills/archive-implementation/scripts/archive_implementation.py --archive-name "<archive name>" --apply
   ```

6. Report the archive folder and moved paths.

## Move Boundary

Preserve:

- Top-level dot-prefixed files and directories.
- Files listed in `.agents/afk-research-manifest.json`.
- Generated conflict files listed in the manifest's `conflicts[].generatedPath`.
- `package.json`, `package-lock.json`, and `node_modules` when the manifest says Sandcastle was enabled or `package.json` was created by setup.

Move:

- Non-hidden project files and directories that are not part of the setup baseline.
- Extra files inside partially managed directories, while leaving the managed files in place.

The helper preserves relative paths under `.archive/<archive-name>/`. For example, `src/app.ts` moves to `.archive/<archive-name>/src/app.ts`.

## Missing Manifest

If `.agents/afk-research-manifest.json` is missing, the dry-run command exits with an error. Explain that the setup baseline cannot be determined safely, then ask the user whether to inspect a conservative fallback plan.

Only after the user confirms, run:

```sh
python3 .agents/skills/archive-implementation/scripts/archive_implementation.py --archive-name "<archive name>" --allow-missing-manifest
```

Do not apply a missing-manifest plan unless the user confirms after seeing the exact move list.

## Archive Names

The script normalizes archive names to lowercase slug form. If `.archive/<normalized-name>/` already exists, stop and ask for a different name; never merge into or overwrite an existing archive.

## Script

Use `scripts/archive_implementation.py` for planning and moving. The script supports:

- `--archive-name <name>`: required.
- `--root <path>`: project root; defaults to the current directory.
- `--allow-missing-manifest`: allow a fallback plan when the manifest is absent.
- `--json`: emit the plan as JSON.
- `--apply`: perform the move.
