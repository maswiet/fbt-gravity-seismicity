<!-- afk-research:managed v1 -->
# GMT remote datasets (earth_relief, earth_faa)

---
title: "GMT remote datasets (earth_relief, earth_faa)"
type: concept
status: active
created: 2026-07-29
updated: 2026-07-29
sources:
  - "[[wiki/sources/gmt-tutorials]]"
tags:
  - gmt
  - datasets
  - gravity
  - topography
---

## Summary

GMT/PyGMT can download curated global grids on demand ("remote datasets"), cached locally. Two are used in this project's real run:

- **earth_relief** — global topography/bathymetry (SRTM15+ / Tozer et al. 2019), multiple resolutions (e.g. `30m`, `15m`, `10m`, ...). Used for the topographic/ocean tesseroid correction.
- **earth_faa** — Earth **free-air gravity anomaly** (IGPP/Sandwell et al. 2019, altimetry-derived), same resolutions. Used as a *proxy* for the gravity disturbance in the `--gravity faa` path.

## Key Points

- Accessed via `pygmt.datasets.load_earth_relief(resolution=..., region=...)` and `pygmt.datasets.load_earth_free_air_anomaly(...)`, returning xarray grids on a (lat, lon) mesh.
- `earth_faa` (free-air anomaly, altimetry) ≠ the satellite **GGM gravity disturbance** used in the paper-faithful path (that comes from GOCO06S via pyshtools — see [[wiki/entities/fatiando-a-terra]] and the plan). The free-air anomaly is a close but not identical quantity; it is the fallback when the GGM synthesis is unavailable.
- Resolution names are angular (e.g. `30m` ≈ 0.5°); choose to match the model grid spacing.

## Links

- Used by: [[wiki/syntheses/moho-indonesia-replication-plan]] (`run_real.py`)
- Feeds: [[wiki/concepts/gravity-data-corrections]]
- Tool: [[wiki/entities/gmt-pygmt]]
- Source: [[wiki/sources/gmt-tutorials]]

## Open Questions

- How large is the earth_faa (free-air anomaly) vs GGM (disturbance) difference over the Indonesian arcs, and does it bias the Moho estimate? (GGM run gave std 6.02 km vs faa 6.27 km against the seismic points.)
