<!-- afk-research:managed v1 -->
# GMT / PyGMT

---
title: "GMT / PyGMT"
type: entity
status: active
created: 2026-07-29
updated: 2026-07-29
sources:
  - "[[wiki/sources/gmt-tutorials]]"
tags:
  - software
  - mapping
  - python
---

## Summary

**GMT (Generic Mapping Tools)** is an open-source toolkit for mapping and plotting geographic/geophysical data; **PyGMT** is its Python interface. GMT also hosts **remote datasets** (earth_relief, earth_faa, ...) served on demand. Both are used in this project for data access and cartography.

## Role in this project

- **Data access:** `run_real.py` fetches real topography (`earth_relief`) and free-air gravity (`earth_faa`) through PyGMT — see [[wiki/concepts/gmt-remote-datasets]].
- **Cartography:** `moho_indonesia/16_results_maps.py` currently uses matplotlib + cartopy for previews; PyGMT (`pygmt 0.17` in the `fbt` env) is available for GMT-quality publication figures.
- Complements [[wiki/entities/fatiando-a-terra]] (Harmonica/Boule), which handles the forward modelling and gravity processing.

## Related

- Reference: [[wiki/sources/gmt-tutorials]]
- Concept: [[wiki/concepts/gmt-remote-datasets]]
- Plan: [[wiki/syntheses/moho-indonesia-replication-plan]]

## Open Questions

- Move final figures to PyGMT for beachballs (seismic stations), hillshaded bathymetry, and consistent CPTs?
