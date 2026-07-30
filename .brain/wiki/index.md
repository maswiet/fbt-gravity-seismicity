<!-- afk-research:managed v1 -->
# Index

This is the content map for the `.brain` second brain. Read this file before answering from or editing the wiki. Update it on every ingest and every durable query that changes the vault.

Last updated: 2026-07-29 — ingested ESDM 2022 sedimentary basin map

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
- [[wiki/sources/gmt-tutorials]] - GMT/PyGMT tutorial site (gmt-tutorials.org); mapping reference for the project figures.
- [[wiki/sources/darman-yuliong-2020-indonesian-sedimentary-basins]] - Berita Sedimentologi 45 review of Indonesian basins + sediment-thickness/depth-to-basement.
- [[wiki/sources/esdm-2022-sedimentary-basin-map-indonesia]] - Official ESDM 2022 map: 128 named basins + areas + tectonic-setting classification.
- [[wiki/sources/kennett-2011-ausmoho]] - AusMoho seismic Moho of Australia; southern-boundary cross-check for our model.

## Concepts

- [[wiki/concepts/tesseroid-forward-modeling]] - Spherical-prism gravity forward modelling (GLQ + adaptive discretization).
- [[wiki/concepts/botts-method-gravity-inversion]] - Efficient iterative interface inversion; diagonal Bouguer-plate Jacobian.
- [[wiki/concepts/regularized-interface-gravity-inversion]] - Nonlinear interface inversion stabilized by Tikhonov smoothness.
- [[wiki/concepts/gravity-inversion-hyperparameters]] - μ, Δρ, z_ref and the two-step cross-validation to estimate them.
- [[wiki/concepts/gravity-data-corrections]] - Disturbance → Bouguer → sediment-free Bouguer inversion input.
- [[wiki/concepts/gmt-remote-datasets]] - GMT earth_relief / earth_faa on-demand grids used by run_real.py.
- [[wiki/concepts/indonesian-sedimentary-basins]] - Basin inventory + sediment thickness (0-9 km); context/cross-check for the sediment correction.

## Entities

- [[wiki/entities/fatiando-a-terra]] - Open-source Python geophysics toolkit (Harmonica lineage) by Uieda; project tooling.
- [[wiki/entities/gmt-pygmt]] - GMT / PyGMT mapping toolkit + remote datasets; used for data access & figures.

## Claims

- No standalone claim pages yet.

## Questions

- [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]] - Fit of the method to Sumatra fore-arc / Flores FBT interface targets (seed).

## Syntheses

- [[wiki/syntheses/moho-indonesia-replication-plan]] - Plan to replicate Uieda & Barbosa (2017) for the whole-Indonesia Moho; pipeline in `moho_indonesia/`.

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
