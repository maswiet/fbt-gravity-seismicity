<!-- afk-research:managed v1 -->
# Moho of Indonesia — replication plan (Uieda & Barbosa 2017)

---
title: "Moho of Indonesia — replication plan (Uieda & Barbosa 2017)"
type: synthesis
status: active
created: 2026-07-28
updated: 2026-07-28
sources:
  - "[[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]"
tags:
  - project-plan
  - moho
  - gravity-inversion
  - indonesia
---

## Objective

Replicate [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]] — **same data types and methodology** — to estimate the **Moho depth of all of Indonesia** from satellite gravity, validated against a seismic Moho compilation. Public data only.

Note: this is a **Moho (crust–mantle) study**, distinct from the earlier-scoped Sumatra fore-arc *basement* idea and the on-disk Flores FBT gravity–seismicity project. See [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]].

## Data mapping (South America → Indonesia)

| Role | Paper | Indonesia (public) |
|---|---|---|
| Satellite gravity | GOCO5S | GOCO06s / XGM2019e / EIGEN-6C4 (ICGEM) |
| Topography/bathymetry | ETOPO1 | ETOPO (+ optional DEMNAS) |
| Sediments | CRUST1.0 | CRUST1.0 |
| Normal gravity | WGS84 closed-form | same (Boule/WGS84) |
| Validation Moho | Assumpção et al. (2013), 937 pts | `Depth_Moho.txt`, **105 receiver-function points** (STAT LON LAT DEPTH), 96–141°E, −10..+5° |

## Method (identical to paper)

Corrections [[wiki/concepts/gravity-data-corrections]] → inversion [[wiki/concepts/regularized-interface-gravity-inversion]] (Bott [[wiki/concepts/botts-method-gravity-inversion]] + Tikhonov + tesseroids [[wiki/concepts/tesseroid-forward-modeling]]) → hyperparameters [[wiki/concepts/gravity-inversion-hyperparameters]] (μ by cross-validation; z_ref, Δρ by validation vs the seismic Moho). Reimplemented on modern **Harmonica** (see [[wiki/entities/fatiando-a-terra]]), which has tesseroid forward modelling but no built-in Bott/Moho inversion.

## Study area & parameters

- Region of interest `94–141°E, 11°S–6°N`; padded computation region `92–143°E, 13°S–8°N` (buffer vs edge effects).
- Grid spacing `0.2°` (~22 km); densities crust 2670, seawater 1030 kg/m³; Moho Δρ estimated (first guess 400).

## Pipeline (repo: `moho_indonesia/`)

`config.py`, `moho_utils.py`, then `10_fetch_grav_topo_sed` → `11_gravity_disturbance` → `12_topographic_correction` → `13_sediment_correction` → `14_moho_inversion` (core) → `15_hyperparameters` → `16_results_maps`.

## Indonesia-specific risks / novelty

- **Subduction slabs (Sunda/Banda) not modelled** → large gravity–seismic Moho mismatches at the arcs (cf. Andes/Nazca). These mismatch maps are a key interpretive product (density anomalies).
- **Station-based (land) validation** → offshore/oceanic Moho unvalidated.
- **Smoothness regularization blurs sharp Moho steps** at trench/arc transitions; sharpness-inducing regularization is a possible extension.

## Status

Scaffold built (structure + core algorithm skeleton; heavy parts are TODO). Validation data staged locally at `data/external/Depth_Moho.txt` (kept local / gitignored pending provenance + publication rights).

## Open questions / next actions

- Confirm depth datum (sea level vs ellipsoid) and **cite the source study** of `Depth_Moho.txt`.
- Choose the exact GGM (GOCO06s vs XGM2019e) and truncation degree; document tide system.
- Implement in order: acquisition (10) → corrections (11–13) → inversion core (14) → hyperparameters (15) → figures (16).
- Consider ingesting method ancestors: Bott (1960), Silva et al. (2014), Uieda et al. (2016).
