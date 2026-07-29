<!-- afk-research:managed v1 -->
# GMT Tutorials (gmt-tutorials.org)

---
title: "GMT Tutorials (gmt-tutorials.org)"
type: source
status: active
created: 2026-07-29
updated: 2026-07-29
source_author: "Whyjay Zheng and contributors"
source_url: "https://gmt-tutorials.org/en/"
raw: "[[raw/2026-07-29_gmt-tutorials/provenance]]"
tags:
  - gmt
  - pygmt
  - mapping
  - tutorial
  - reference
---

## Summary

A comprehensive, community-maintained tutorial site (Jupyter Book) for **Generic Mapping Tools (GMT 6)** and its Python interface **PyGMT** — open-source software for mapping and plotting geographic data. Step-by-step, code-first. Dual-licensed MIT (code) + CC-BY 4.0 (content). Directly relevant reference for producing the Moho maps in this project (`moho_indonesia/16_results_maps.py`, `run_real.py`), which use PyGMT/GMT.

## Key Points (site structure)

1. **Introduction & Overview** — installation, basic concepts.
2. **Fundamental Mapping Skills** — first maps, coloring (CPTs), scatter plots.
3. **Common Map Types (beginner)** — raster data, vector plotting, layout, hillshading.
4. **Advanced Map Types** — 3D visualization, focal mechanisms (beachballs), image draping.
5. **Grid Data Processing** — raster calculations and image processing.
6. **Numerical Data Analysis** — statistics, histograms, regression.
7. **Appendices** — references, command index, gallery.

Teaches GMT 6 modern syntax (with GMT 4/5 legacy notes), PyGMT, and shell/Python scripting.

## Why it matters here

- Reference for improving the project's figures (CPTs, hillshading, layout, focal mechanisms for the seismic context) beyond the current matplotlib/cartopy previews.
- The project already relies on GMT **remote datasets** via PyGMT — see [[wiki/concepts/gmt-remote-datasets]].

## Extracted Concepts

- [[wiki/concepts/gmt-remote-datasets]]

## Extracted Entities

- [[wiki/entities/gmt-pygmt]]

## Conflicts / Updates

- None.

## Open Questions

- Should the final publication figures move from matplotlib/cartopy to PyGMT for GMT-quality cartography (beachballs for the seismic Moho stations, hillshaded bathymetry)? See [[wiki/entities/gmt-pygmt]].
