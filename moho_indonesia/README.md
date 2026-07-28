# Moho of Indonesia — gravity inversion (replication)

Replication of **Uieda & Barbosa (2017)**, *"Fast nonlinear gravity inversion in
spherical coordinates with application to the South American Moho"* (GJI 208,
162–176, doi:10.1093/gji/ggw390), applied to **all of Indonesia** with the same
data types and methodology, using public data only.

> Method knowledge base: see `.brain/wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion.md`
> and linked concept pages, plus `.brain/wiki/syntheses/moho-indonesia-replication-plan.md`.

## Pipeline

Scripts are numbered and run in order. Each reads the previous stage's output
(NetCDF grids under `data/processed/moho/`) and writes the next.

| Script | Stage | Paper ref |
|---|---|---|
| `config.py` | Central config: region, spacing, densities, paths, hyperparameter ranges | — |
| `moho_utils.py` | Shared helpers: grid I/O, tesseroid model, roughness matrix, data loading | — |
| `10_fetch_grav_topo_sed.py` | Acquire GGM gravity (ICGEM), ETOPO topography, CRUST1.0 sediments | Data |
| `11_gravity_disturbance.py` | Gravity disturbance `δ = g − γ` (Boule/WGS84) | eq. 1 |
| `12_topographic_correction.py` | Tesseroid topo/ocean effect → **Bouguer disturbance** | eq. 2, Fig. 8 |
| `13_sediment_correction.py` | CRUST1.0 sediment effect → **sediment-free Bouguer** (inversion input) | Fig. 9a |
| `14_moho_inversion.py` | **Bott + Tikhonov + tesseroids** Gauss-Newton inversion (core) | eq. 13–15 |
| `15_hyperparameters.py` | `μ` by cross-validation; `z_ref, Δρ` by validation vs seismic Moho | Fig. 7, 10 |
| `16_results_maps.py` | Final inversion + Moho map, residuals, difference-from-seismic | Fig. 11, 12 |

Run, e.g.:

```bash
conda activate fbt
python moho_indonesia/11_gravity_disturbance.py
```

## Data

- **Gravity (satellite):** GOCO06s / XGM2019e from the [ICGEM](http://icgem.gfz-potsdam.de/) calculation service → `data/raw/gravity/`.
- **Topography/bathymetry:** ETOPO → `data/raw/topography/`.
- **Sediments:** CRUST1.0 (Laske et al. 2013) → `data/external/crust1.0/`.
- **Validation Moho:** `data/external/Depth_Moho.txt` — 105 seismic (receiver-function) Moho points, columns `STAT LON LAT DEPTH(km)`, spanning 96–141°E, −10..+5°. *TODO: confirm depth datum and cite the source study.*

## Study area & key parameters (see `config.py`)

- Region of interest: `94–141°E, 11°S–6°N`; padded computation region `92–143°E, 13°S–8°N` (buffer against inversion edge effects).
- Grid spacing: `0.2°` (~22 km).
- Densities: crust 2670, seawater 1030 kg/m³; Moho `Δρ` estimated (first guess 400).

## Status

**Scaffold** — structure, data flow, and the core algorithm are laid out; the
heavy pieces are marked `TODO` / `NotImplementedError`. Fill in, in order:
data acquisition (10) → corrections (11–13) → inversion core (14: tesseroid
forward model + roughness matrix) → hyperparameters (15) → figures (16).

## Notes / risks specific to Indonesia

- Subducting Sunda/Banda slabs are **not** modelled → expect large gravity-seismic
  Moho mismatches at the arcs (cf. the Andes/Nazca issue in the paper).
- Seismic Moho control is **station-based (land)** → offshore/oceanic Moho is not
  directly validated.
- Smoothness regularization blurs sharp Moho steps; consider sharpness-inducing
  alternatives if arc/trench transitions matter.
