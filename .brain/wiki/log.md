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

## [2026-07-28] maintenance | Implement + test inversion core (14)

- **Trigger:** user asked to continue implementation.
- **Files changed (code):** `moho_indonesia/14_moho_inversion.py` (full Bott+Tikhonov loop, injectable forward, `--selftest`), `moho_indonesia/moho_utils.py` (real finite_difference_matrix, Bouguer-plate forward, tesseroid model builder + Harmonica forward, lazy heavy imports), `moho_indonesia/README.md` (status).
- **Files changed (.brain):** `wiki/syntheses/moho-indonesia-replication-plan.md` (status), `wiki/log.md` (this entry).
- **Key result:** inversion machinery verified — synthetic self-test recovers a known Moho at RMS 0.027 km, 3 iterations. Runs with numpy/scipy only (no harmonica/download needed). Real tesseroid forward implemented, pending `fbt` env + input grids.
- **Follow-ups:** implement acquisition (10) + corrections (11–13) to produce a real sediment-free Bouguer grid, then run the tesseroid inversion end-to-end; then 15 (hyperparameters) and 16 (figures).

## [2026-07-28] maintenance | Implement acquisition + corrections (10-13)

- **Trigger:** user asked to continue with steps 10-13.
- **Files changed (code):** `moho_indonesia/10_fetch_grav_topo_sed.py` (pooch downloads: ICGEM manual-fallback, ETOPO 2022, CRUST1.0; + subset/unpack), `11_gravity_disturbance.py` (load ICGEM .gdf or observed − WGS84 normal gravity), `12_topographic_correction.py` (topo/ocean tesseroids → Bouguer), `13_sediment_correction.py` (CRUST1.0 sediment tesseroids → sediment-free Bouguer), `moho_utils.py` (topography_to_tesseroids, layer_to_tesseroids, tesseroid_gravity_grid, load_crust1_sediments), `environment.yml` (+pooch), `README.md`.
- **Files changed (.brain):** synthesis status, this log entry.
- **Key result:** full correction chain implemented. Tesseroid geometry builders unit-tested numpy-only (bottom<=top, land/ocean & sediment density signs, radius mapping); inversion self-test still passes. End-to-end tesseroid forward NOT run (needs `fbt` env + network + data).
- **Verify before trusting:** ICGEM tide system; ETOPO netCDF var/coord names; CRUST1.0 column order + sign in `load_crust1_sediments`.
- **Follow-ups:** run 10→14 end-to-end in `fbt` (start coarse, e.g. 0.4°); then implement 15 (hyperparameters) and 16 (figures).

## [2026-07-28] maintenance | Implement hyperparameters (15) + figures (16) + preview

- **Trigger:** user asked to continue with 15/16 and wanted to review a map/figure.
- **Files changed (code):** `moho_indonesia/15_hyperparameters.py` (masked Bott+Tikhonov CV for μ; z_ref/Δρ validation vs seismic Moho; MSE curve/surface plot), `16_results_maps.py` (final inversion + Moho/residual/difference figures via matplotlib+cartopy; `--demo` preview mode), `README.md`.
- **Files changed (.brain):** synthesis status, this log entry.
- **Key result:** all pipeline steps 10–16 implemented. Rendered preview figures (`figures/moho/preview_*.png`) from the REAL 105 seismic Moho points + a synthetic Moho background; coastlines render fine. Sent to user for design review. Real hyperparameter/inversion runs still need the `fbt` env + data.
- **Note:** preview PNGs left untracked (regenerable via `16 --demo`). Depth_Moho.txt still local-only pending provenance.
- **Follow-ups:** run end-to-end in `fbt`; cite Depth_Moho.txt source; verify ICGEM tide / ETOPO vars / CRUST1.0 columns.

## [2026-07-28] maintenance | First REAL end-to-end run + sign-bug fix

- **Trigger:** user asked to set up the real run (demo background was "hallucinated").
- **Environment:** discovered the `fbt` conda env exists with harmonica 0.7 / verde 1.9 / boule 0.6 / pooch 1.9 / pygmt 0.17, and network works. Ran with `/opt/homebrew/Caskroom/miniforge/base/envs/fbt/bin/python`.
- **New file:** `moho_indonesia/run_real.py` — coarse real run using GMT `earth_relief` + `earth_faa` (Sandwell/IGPP) via pygmt, tesseroid Bouguer correction, Bott+Tikhonov inversion, figures + seismic validation.
- **BUG FIXED (sign):** `moho_to_tesseroids` had the density-contrast sign backwards (deeper Moho → +anomaly; physically should be −). Fixed to match paper Fig. 1f (deeper → −Δρ); made `forward_gravity_bouguer_plate` and the inversion Jacobian `a = -2πGΔρ` consistent (files `moho_utils.py`, `14`, `15`). Self-test still passes (RMS 0.028 km) and tesseroid forward now gives deeper→negative. Also fixed an importlib `@dataclass` load error by registering loaded modules in `sys.modules` (`16`, `run_real`).
- **Result:** real 0.5° Moho of Indonesia — thick (~35–40 km) under Sumatra/Java/arc, thin (~5–15 km) oceanic; converged 13 iters, RMS 0.54 mGal; difference vs 105 seismic points mean −4.55 km, std 6.27 km (paper std 6.8 km). Figures `figures/moho/real_*.png` (untracked, regenerable).
- **Follow-ups:** swap in real GGM disturbance (ICGEM); add CRUST1.0 sediments; calibrate hyperparameters (15); finer grid; handle oceanic shallow/negative artefacts; cite Depth_Moho.txt source.
