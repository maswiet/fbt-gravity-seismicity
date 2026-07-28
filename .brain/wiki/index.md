<!-- afk-research:managed v1 -->
# Index

This is the content map for the `.brain` second brain. Read this file before answering from or editing the wiki. Update it on every ingest and every durable query that changes the vault.

Last updated: 2026-07-28 — first ingest (Uieda & Barbosa 2017)

## Start Here

- [[AGENTS|AGENTS.md]] - Operating schema for the LLM wiki agent.
- [[CLAUDE|CLAUDE.md]] - Claude-compatible pointer to the schema.
- [[wiki/log|log.md]] - Append-only chronological activity log.

## Folder Conventions

- `raw/` - Immutable source captures and provenance records.
- `wiki/` - All maintained knowledge and operating files.
- `wiki/index.md` - This content map.
- `wiki/log.md` - Append-only activity log.
- `wiki/sources/` - Source summaries and extracted takeaways.
- `wiki/concepts/` - Durable ideas and patterns.
- `wiki/entities/` - People, organizations, projects, datasets, and named things.
- `wiki/claims/` - Evidence-bearing claims worth tracking.
- `wiki/questions/` - Research questions and durable answers.
- `wiki/syntheses/` - Multi-source analysis and evolving theses.
- `wiki/outputs/` - Exportable artifacts and examples.
- `wiki/templates/` - Reusable page templates and workflow checklists.
- `wiki/inbox/` - Unprocessed material waiting for ingest.
- `wiki/scratch/` - Temporary agent work notes.
- `wiki/archive/` - Superseded or inactive material.

## Sources

- [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]] - Uieda & Barbosa (2017), GJI: fast nonlinear gravity inversion in spherical coords; South American Moho.

## Concepts

- [[wiki/concepts/tesseroid-forward-modeling]] - Spherical-prism gravity forward modelling (GLQ + adaptive discretization).
- [[wiki/concepts/botts-method-gravity-inversion]] - Efficient iterative interface inversion; diagonal Bouguer-plate Jacobian.
- [[wiki/concepts/regularized-interface-gravity-inversion]] - Nonlinear interface inversion stabilized by Tikhonov smoothness.
- [[wiki/concepts/gravity-inversion-hyperparameters]] - μ, Δρ, z_ref and the two-step cross-validation to estimate them.
- [[wiki/concepts/gravity-data-corrections]] - Disturbance → Bouguer → sediment-free Bouguer inversion input.

## Entities

- [[wiki/entities/fatiando-a-terra]] - Open-source Python geophysics toolkit (Harmonica lineage) by Uieda; project tooling.

## Claims

- No standalone claim pages yet.

## Questions

- [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]] - Fit of the method to Sumatra fore-arc / Flores FBT interface targets (seed).

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
- Brain operations that change `.brain` must commit and push those `.brain` changes to the repository remote before reporting completion.
- Brain imports are non-destructive: imported knowledge enriches the current vault, while schema and operational-file collisions are preserved as provenance unless explicitly approved.
- Brain setup should also ensure generated export/import artifacts under `.outputs/` are ignored by Git.
