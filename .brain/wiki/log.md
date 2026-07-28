<!-- afk-research:managed v1 -->
# Log

Append-only chronological record for the `.brain` second brain. Use headings in this format:

```markdown
## [YYYY-MM-DD] type | Title
```

Allowed types: `setup`, `ingest`, `query`, `lint`, `maintenance`, `export`, `import`, `schema`.

## [2026-07-28] ingest | Uieda & Barbosa (2017) — spherical gravity inversion (South American Moho)

- **Trigger:** user ran `/ingest` on `/Users/maswiet/Downloads/ggw390.pdf` (GJI 208, 162–176; doi:10.1093/gji/ggw390).
- **Files changed:**
  - `raw/2026-07-28_uieda-barbosa-2017-spherical-gravity-inversion/ggw390.pdf` (immutable, 0444)
  - `raw/2026-07-28_uieda-barbosa-2017-spherical-gravity-inversion/provenance.md`
  - `wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion.md`
  - `wiki/concepts/tesseroid-forward-modeling.md`
  - `wiki/concepts/botts-method-gravity-inversion.md`
  - `wiki/concepts/regularized-interface-gravity-inversion.md`
  - `wiki/concepts/gravity-inversion-hyperparameters.md`
  - `wiki/concepts/gravity-data-corrections.md`
  - `wiki/entities/fatiando-a-terra.md`
  - `wiki/questions/applying-spherical-gravity-inversion-to-indonesia.md`
  - `wiki/index.md` (Sources/Concepts/Entities/Questions + timestamp)
  - `wiki/log.md` (this entry)
- **Key result:** first source ingested. Captured the tesseroid + Bott + Tikhonov regularized interface-inversion method, its three hyperparameters (μ, Δρ, z_ref) and cross-validation strategy, the gravity-correction chain, and the Fatiando/Harmonica tooling link. Connected to the project via a seed question on applying the method to Sumatra fore-arc / Flores FBT targets.
- **Follow-ups:** develop the seed question once interface target + study-area extent are fixed; inventory public datasets and independent depth constraints; consider ingesting Bott (1960), Silva et al. (2014), and Uieda et al. (2016) as method ancestors.

## [2026-07-28] maintenance | Moho-Indonesia replication plan + code scaffold

- **Trigger:** user decided to replicate Uieda & Barbosa (2017) for the whole-Indonesia Moho (same data types + methodology, public data only) and asked to scaffold the pipeline.
- **Files changed (.brain):**
  - `wiki/syntheses/moho-indonesia-replication-plan.md` (new)
  - `wiki/index.md` (Syntheses entry + timestamp)
  - `wiki/log.md` (this entry)
- **Code scaffold (separate commit, repo track `moho_indonesia/`):** config.py, moho_utils.py, _bootstrap.py, 10–16 numbered scripts, README.md. All syntax-valid; config + Moho loader verified against `data/external/Depth_Moho.txt` (105 points parsed).
- **Key result:** durable plan recorded; pipeline structure + Bott/Tikhonov core algorithm skeleton in place with TODOs.
- **Follow-ups:** confirm `Depth_Moho.txt` depth datum + cite source study; pick exact GGM; implement 10→16 in order. Validation Moho kept local (gitignored) pending provenance/publication rights.
