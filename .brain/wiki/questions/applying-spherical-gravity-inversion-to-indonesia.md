<!-- afk-research:managed v1 -->
# Can the Uieda–Barbosa spherical inversion be applied to Indonesian interface targets?

---
title: "Can the Uieda–Barbosa spherical inversion be applied to Indonesian interface targets?"
type: question
status: seed
created: 2026-07-28
updated: 2026-07-28
sources:
  - "[[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]"
tags:
  - open-question
  - project-fit
  - gravity-inversion
---

## Question

Is the regularized tesseroid + Bott + Tikhonov inversion of [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]] a suitable method for the group's Indonesian gravity work — e.g. **basement/basin architecture of the Sumatra fore-arc** or the **Flores back-arc thrust (FBT)** — using public data only?

## Why it matters

The method is public-data-friendly (satellite gravity), open-source (Fatiando/Harmonica lineage), and directly targets interface relief (Moho or basement) — the core deliverable of both the Sumatra fore-arc and FBT projects.

## Working notes / sub-questions

- **Interface target:** Moho (as in the paper) vs sediment–basement contact (fore-arc/back-arc basins). Method is interface-agnostic but `Δρ`, `z_ref` differ (basement `Δρ` is sediment-vs-basement, not crust-vs-mantle).
- **Spherical vs planar:** Is tesseroid (spherical) modelling needed at Sumatra/Flores study-area extents, or is a planar prism approach adequate? Regional (~1000+ km) → lean spherical; single-basin → planar may suffice. See [[wiki/concepts/tesseroid-forward-modeling]].
- **Data:** which public gravity (GOCO5S, XGM2019e, EGM2008, GGMplus, Sandwell altimetry offshore), topo/bathy (ETOPO, DEMNAS, GEBCO), and sediment models drive the corrections in [[wiki/concepts/gravity-data-corrections]]?
- **Validation depths for `z_ref`/`Δρ`:** what independent constraints exist (well tops, seismic reflection, receiver-function Moho, Slab2)? Offshore fore-arc has few wells.
- **Regularization choice:** fault-bounded basement steps may need sharpness-inducing regularization rather than smoothness. See [[wiki/concepts/regularized-interface-gravity-inversion]].
- **Bias risk:** unmodelled density anomalies (volcanic/igneous bodies, subducting slab) bias the estimate, as the paper found in the Andes and Amazonas/Paraná. The subduction setting of both Indonesian targets makes this a first-order concern.

## Status

Seed — to be developed once the project's specific interface target and study-area extent are fixed. Related project context: the on-disk project is the Flores FBT gravity–seismicity workflow; an earlier discussion scoped a Sumatra fore-arc basement dissertation.

## Next Actions

- Decide interface target (Moho vs basement) and study-area extent per sub-project.
- Inventory available public datasets and independent depth constraints.
- Prototype the correction → inversion chain in Harmonica on a small test area.
