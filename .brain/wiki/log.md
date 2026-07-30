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

## [2026-07-29] maintenance | Paper-faithful GGM gravity (GOCO06S via pyshtools)

- **Trigger:** user chose the "exact paper" satellite GGM gravity path.
- **Environment:** installed `pyshtools` 4.14 into the `fbt` env (pip); added to environment.yml.
- **New file:** `moho_indonesia/ggm_gravity.py` — synthesises the GOCO06S gravity disturbance (pyshtools.datasets.Earth.GOCO06S) on the WGS84 ellipsoid at the computation height, with `omega` set and `expand(a=WGS84.a, f=WGS84.f, normal_gravity=True)`. Fixed a ~1600 mGal offset caused by evaluating on the sphere r0 without the ellipsoid/centrifugal reference.
- **Changed:** `run_real.py` now takes `--gravity ggm|faa`; `config.GGM_NAME='GOCO06S'`; README.
- **Result (GGM, 0.5°):** disturbance −216..224 mGal; Moho map smoother/more coherent than faa; difference vs 105 seismic points mean −4.97 km, std 6.02 km (paper 6.8). Figures `figures/moho/real_*_ggm.png`.
- **Follow-ups:** add CRUST1.0 sediments; calibrate hyperparameters (15); finer grid; oceanic artefacts; cite Depth_Moho.txt.

## [2026-07-29] ingest | GMT Tutorials (gmt-tutorials.org)

- **Trigger:** user ran `/ingest https://gmt-tutorials.org/en/`.
- **Files changed:**
  - `raw/2026-07-29_gmt-tutorials/provenance.md`
  - `wiki/sources/gmt-tutorials.md`
  - `wiki/entities/gmt-pygmt.md`
  - `wiki/concepts/gmt-remote-datasets.md`
  - `wiki/index.md` (Sources/Concepts/Entities + timestamp)
  - `wiki/log.md` (this entry)
- **Key result:** captured the GMT 6 / PyGMT tutorial reference (Whyjay Zheng; MIT + CC-BY 4.0). Linked it to the project's actual use of PyGMT (figures) and GMT remote datasets (earth_relief, earth_faa in run_real.py). Only the landing page/TOC was captured, not every chapter.
- **Follow-ups:** consider moving publication figures from matplotlib/cartopy to PyGMT (beachballs for seismic stations, hillshaded bathymetry, consistent CPTs).

## [2026-07-29] maintenance | Hyperparameter calibration (step 15) on real data

- **Trigger:** user asked to calibrate hyperparameters (step 15).
- **New file:** `moho_indonesia/calibrate.py` — two-step calibration reusing run_real's data prep (faa or ggm). Adds Moho depth clipping (3–70 km) each iteration to stop the negative-depth overshoot that had put tesseroids above the computation height ("point inside tesseroid" warnings).
- **Result (faa, 0.5°):** μ=1e-10 (CV), then grid search → z_ref=35 km, Δρ=500 kg/m³. Difference vs 105 seismic points improved to **mean +1.40 km, std 6.02 km** (from −4.55 / 6.27 uncalibrated; paper 1.2 / 6.8). Moho 7–59 km, no negative artefacts. Rewrote GRID_MOHO + hyperparameters.json; regenerated the PyGMT map.
- **Context:** user extended run_real with `--gravity ggm` (GOCO06S via new `ggm_gravity.py`); calibrate.py supports `--gravity ggm` for the paper-faithful path.
- **Staged (not yet applied):** copied Pak Wiwit's Indonesian tectonics to `data/external/tectonics/` (trench_edit, sesar_naik/turun/mendatar, antiklin, sinklin, patahan_aktif; gitignored). Volcano locations (`volcano_loc.txt`) not in the source folder — still needed.
- **Follow-ups:** overlay real tectonics on the maps; get volcano locations; calibrate on the GGM path; add sediments; finer grid.

## [2026-07-29] maintenance | GGM calibration + real tectonics + volcanoes on map

- **Trigger:** user chose the GGM path + public volcano source.
- **GGM calibration** (`calibrate.py --gravity ggm`, GOCO06S via pyshtools 4.14): μ=1e-10, z_ref=35 km, Δρ=500 → difference vs seismic **mean +1.11 km, std 5.78 km** — best yet (faa gave +1.40/6.02; paper 1.2/6.8). GOCO06S is the successor of the paper's GOCO5S. GRID_MOHO now holds the GGM-calibrated result.
- **Volcanoes:** fetched Smithsonian GVP Holocene volcanoes via WFS (`webservices.volcano.si.edu/geoserver/GVP-VOTW`), filtered to the Indonesia bbox → 101 volcanoes at `data/external/tectonics/volcano_loc.txt` (lon lat elev). Plotted as red triangles (the custom volcano.def symbol path failed in GMT; triangle is robust). They trace the Sunda-Banda arc.
- **Map:** `plot_pygmt.py` now overlays real Pak Wiwit tectonics + GVP volcanoes on the GGM-calibrated Moho. High-res GSHHG coast, thin frame, smoothed contours.
- **Provenance to record for the write-up:** Pak Wiwit tectonics source; GVP citation; GOCO06S (Kvas et al. 2021); Depth_Moho.txt source.
- **Follow-ups:** add CRUST1.0 sediments; finer grid; run the full 10-16 pipeline on the GGM path end-to-end.

## [2026-07-29] maintenance | CRUST1.0 sediment correction — implemented + finding

- **Trigger:** user asked to add the CRUST1.0 sediment correction.
- **Done:** downloaded CRUST1.0 (UCSD) to `data/external/crust1.0/`; verified `load_crust1_sediments` against the real files (bnds/rho are 9-col; sediments = layers 2-4; ordering 89.5→-89.5 lat, -179.5→179.5 lon). Fixed two bugs: `layer_to_tesseroids` density broadcast (2D contrast → raveled), and absent CRUST1.0 layers (rho==0) now get zero contrast. Added `calibrate.py --sediments`. Sediment thickness over Indonesia 0–8.7 km (mean 1.44); sediment gravity effect −191..−3 mGal (median −36).
- **Finding (honest):** on the coarse 0.5° grid the sediment correction **worsens** the fit to the 105 seismic points: GGM+sediments mean −1.59 km, std 6.37 km vs GGM-only mean +1.11 km, **std 5.78 km**. Reason: the seismic Moho is **station-based (land)**, where CRUST1.0 sediments are thin/uncertain, while the correction mainly reshapes offshore basins that the validation does not sample. So the sediment-corrected model is more physically complete but not confirmable here. **Best model kept = GGM without sediments.**
- **Follow-ups:** revisit sediments with finer resolution and/or offshore Moho constraints; the correction stays available via `--sediments`.

## [2026-07-29] ingest | Darman & Yuliong (2020) — Sedimentary Basins of Indonesia

- **Trigger:** user ran `/ingest` on two PDFs; this is source 1 of 2 (`minarwan,+bsed450139.pdf`).
- **Files changed:** `raw/2026-07-29_darman-yuliong-2020-sedimentary-basins/provenance.md`, `wiki/sources/darman-yuliong-2020-indonesian-sedimentary-basins.md`, `wiki/concepts/indonesian-sedimentary-basins.md`, `wiki/index.md`, `wiki/log.md`.
- **Key result:** captured Indonesian basin inventory (60/86/128 by author), sediment-thickness maps (Hardy 1997 & Darman/Indogeo, 0–9 km), per-basin depth-to-basement, and the gravity-derived Badan Geologi (2009) basin map. Cross-checks our CRUST1.0 sediment thickness (0–8.7 km) and flags an Indonesia-specific sediment map as a potential replacement. PDF kept local (copyright).
- **Follow-ups:** source 2 next (peta cekungan sedimen Indonesia 2022).

## [2026-07-29] ingest | ESDM (2022) Sedimentary Basin Map of Indonesia

- **Trigger:** source 2 of 2 from the `/ingest` (`content-peta-cekungan-sedimen-indonesia-2022.pdf`).
- **Files changed:** `raw/2026-07-29_esdm-2022-sedimentary-basin-map/provenance.md`, `wiki/sources/esdm-2022-sedimentary-basin-map-indonesia.md`, `wiki/concepts/indonesian-sedimentary-basins.md` (added tectonic classification A–K + official 128-basin inventory), `wiki/index.md`, `wiki/log.md`.
- **Key result:** the official ESDM 2022 basin map — 128 named basins with areas and a tectonic-setting classification (A back-arc … C fore-arc … D trench … F passive margin …). Definitive inventory; the fore-arc (C) basins match the earlier fore-arc dissertation idea. Merged into the existing `indonesian-sedimentary-basins` concept rather than duplicating. PDF kept local (copyright).
- **Follow-ups:** consider digitizing basin outlines as an Indonesia-specific sediment/basement prior for the inversion; overlay basin outlines on the Moho/tectonic map.

## [2026-07-29] maintenance | 0.25° high-res inversion + 3-panel plots (full/west/east)

- **Trigger:** user asked for a 0.25° high-resolution result and split west/east tectonic panels.
- **New:** `hires_moho.py` — single inversion at a given spacing using the calibrated hyperparameters from hyperparameters.json (GGM, clipped 3–70 km). `plot_pygmt.py` parametrized (region, tectonics, volcanoes) and its `__main__` now renders 3 panels: `moho_full_clean.png` (whole Indonesia, no tectonics), `moho_west.png` (94–120°E + all tectonics), `moho_east.png` (115–141°E + all tectonics; overlaps 115–120 with west).
- **FINDING:** the 0.25° grid (13,041 cells) does NOT improve the seismic fit — it slightly worsens it (mean +3.18 km, std 7.97 km vs 0.5° mean +1.11, std 5.78). With μ≈0 the finer mesh overfits short-wavelength gravity/topo-correction residuals and hits the 70 km clip; the resolution limit is the **GGM gravity signal (~0.5°, d/o 300)**, not the grid. Higher resolution needs more regularization and/or finer gravity data. The 0.5° GGM model remains the best-validated (regenerate with `calibrate.py --gravity ggm`).
- **Note:** GRID_MOHO currently holds the 0.25° result (for the high-res figures).
- **Follow-ups:** if finer detail is wanted, increase μ at 0.25° or use a higher-degree combined GGM (e.g. XGM2019e).

## [2026-07-29] maintenance | High-res gravity at 0.25° — XGM2019e vs altimetry (faa)

- **Trigger:** user asked to try XGM2019e for genuinely higher-resolution gravity at 0.25°.
- **XGM2019E failed to download:** pyshtools fetches the full d/o 2159 coefficient file (~281 MB); the connection (~46 kB/s) broke at 17 MB (would take >1.5 h). Added `hires_moho.py --model/--lmax` for when a faster connection is available. EIGEN_6C4 / EGM2008 are similarly large.
- **Practical high-res source = `earth_faa`** (Sandwell/IGPP altimetry free-air anomaly, ~2 km offshore) — already cached via GMT, genuinely finer than GOCO06S (~0.5°), and is essentially what XGM2019e's high degrees encode offshore.
- **Result (faa, 0.25°):** difference vs seismic **mean +0.91 km, std 6.94 km** — better than GGM 0.25° (3.18/7.97) and near-zero bias; cleaner, more coherent map. Std still > 0.5° (5.78) because the smooth station-based seismic Moho cannot validate the added short-wavelength detail (resolution-vs-validation tradeoff). GRID_MOHO now holds faa-0.25°; 3 panels regenerated.
- **Bottom line:** for best seismic-validated numbers use GGM 0.5°; for the most detailed map use faa 0.25°. True 0.25° improvement needs a high-degree combined GGM (XGM2019e) downloaded on a faster link.

## [2026-07-29] maintenance | Draft manuscript

- **Trigger:** user asked for a publishable-assessment + draft manuscript narrative to review.
- **Assessment:** publishable as a regional geophysics study (e.g. J. Asian Earth Sci. / J. Applied Geophysics / IPA-HAGI proceedings), NOT a top-tier novelty paper — it is a faithful replication of Uieda & Barbosa (2017) applied to Indonesia, with honest limitations (coarse resolution, land-biased validation, inconclusive sediments).
- **New file:** `manuscript/moho-indonesia-manuscript-draft.md` — full draft (abstract → conclusions + references + figure list + author checklist), using the actual pipeline numbers. Placeholders flagged: author names/affiliation, seismic-Moho compilation citation + depth datum, active-fault ("Pak Wiwit") citation, previous-work comparison.
- **Follow-ups:** user review; fill placeholders; add previous-work comparison; pick target journal + final featured model.

## [2026-07-29] query | Southern-boundary check vs AusMoho (Kennett et al. 2011)

- **Trigger:** user asked whether our southern-edge Moho is consistent with AusMoho where Indonesia borders Australia.
- **Result:** CONSISTENT over the Australian continental margin — our Arafura/Arnhem-approach Moho (~33–37 km; extracted from GRID_MOHO along 132–140°E, −10 to −10.5°S) matches AusMoho's northern continental crust (~35–40 km) within a few km. At the Timor–Banda collision (124–126°E) our model is much thicker (39–50 km) = real collisional thickening outside AusMoho's coverage (~50 km possibly overestimated). Caveats: our −11° row is a non-padded edge; AusMoho's far north is sparsely constrained.
- **Files:** new `wiki/sources/kennett-2011-ausmoho.md`; added the AusMoho comparison to the manuscript's previous-work paragraph; index/log updated.
- **Follow-ups:** for a rigorous test, obtain the gridded AusMoho surface (Geoscience Australia / IRIS EMC) and difference it against ours in the 118–141°E, 9–11°S overlap; extend the study region south (pad beyond −11°) to remove the edge effect at the border.

## [2026-07-30] maintenance | Extend region south + quantitative AusMoho validation

- **Trigger:** user provided AusMoho/AuSREM grids and asked to extend the domain south and validate against AusMoho.
- **Data:** of the four files, `AusMoho2012.xyz` is the Moho grid (lat lon depth, 0.5°, lat −44..−10); the others (AM4, ACM50, AuSREM-C) are AuSREM velocity models, not Moho — not used. Copied to `data/external/ausmoho/` (gitignored, third-party).
- **Region extended:** `config.REGION` south from −11° to **−15°** (padded −17°) so the Australian margin is interior (edge effect moved to −15°) and overlaps AusMoho. Re-ran `hires_moho.py --spacing 0.5 --gravity ggm`; fit to the Indonesian seismic points 2.53 km / 6.46 km (slightly worse than the −11° domain because the domain/edge changed).
- **RESULT (independent validation):** over northern-Australia mainland (−15..−11.5°S, N=369) our Moho vs AusMoho: mean **−0.14 km**, std **4.84 km**, RMSE 4.84, **r=0.86**. Full overlap (N=477): +0.73/5.83, r=0.76. Figure `figures/moho/ausmoho_comparison.png`. Strong external confirmation (independent gravity vs seismic). Deviations: deepest cratonic crust slightly underestimated; Timor collision over-thickened (~50 km).
- **Manuscript updated:** abstract + new "Independent validation against AusMoho" paragraph + figure 5.
- **Follow-ups:** the main map panels now span to −15° (GRID_MOHO = extended GGM 0.5°); regenerate/crop panels if a −11° Indonesia framing is wanted for final figures. Consider re-calibrating on the extended domain.

## [2026-07-30] maintenance | Re-calibrate on −15° domain + full figure set (Uieda-style)

- **Trigger:** user asked to re-calibrate on the extended domain, regenerate all panels, and add relevant Uieda & Barbosa figure types.
- **Re-calibration** (`calibrate.py --gravity ggm`, −15° domain): μ=1e-10, z_ref=35, Δρ=500 (unchanged); Indonesian seismic fit restored to **mean +1.19 km, std 5.75 km** (the uncalibrated hires run had drifted to 6.46). GRID_MOHO now the calibrated extended model.
- **Added Uieda-Barbosa-style figures:** `calibrate.py` now writes `hyperparameters.png` (Fig. 10 equiv: μ CV curve + (z_ref,Δρ) validation surface); new `validation_seismic.png` (Fig. 12b equiv: residual at the 105 stations + histogram).
- **Panels regenerated** at −15° (full/west/east); west/east extended south to −15 to show the AusMoho overlap zone; fixed the full-panel title ("satellite gravity", not "0.25 deg").
- **AusMoho re-check (recalibrated):** mainland (N=369) mean −0.12, std 4.70, r=0.86; full (N=477) +0.75, std 5.43, r=0.79 — slightly better than before. Manuscript numbers + figure list updated.
- **Follow-ups:** user review; the map panels can be cropped to −11° for an "Indonesia-only" framing if preferred for the final figures.

## [2026-07-30] maintenance | Polish the seismic-validation figure

- **Trigger:** user asked to make validation_seismic prettier — equal panels, high-res coastline, compact colourmap.
- **New file:** `moho_indonesia/plot_validation.py` — regenerates `validation_seismic.png` with two equal-size panels, 10m coastline + soft land/ocean fills, a short horizontal RdBu_r colourbar under the map, and a polished histogram (mean line + ±1σ band). mean +1.19, std 5.75 km, N=105.
