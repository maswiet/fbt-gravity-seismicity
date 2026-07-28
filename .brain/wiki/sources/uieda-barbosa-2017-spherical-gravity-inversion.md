<!-- afk-research:managed v1 -->
# Uieda & Barbosa (2017) — Fast nonlinear gravity inversion in spherical coordinates

---
title: "Uieda & Barbosa (2017) — Fast nonlinear gravity inversion in spherical coordinates"
type: source
status: active
created: 2026-07-28
updated: 2026-07-28
source_author: "Leonardo Uieda; Valéria C.F. Barbosa"
source_created: 2016-10-13
source_url: "https://doi.org/10.1093/gji/ggw390"
raw: "[[raw/2026-07-28_uieda-barbosa-2017-spherical-gravity-inversion/ggw390.pdf]]"
tags:
  - gravity-inversion
  - moho
  - tesseroids
  - spherical-earth
  - methods
---

## Summary

A regularized **nonlinear gravity inversion** to estimate the relief of an interface (the Moho) in **spherical coordinates**, with a low computational footprint. The method combines three ingredients: **Bott's (1960) method** (which avoids building/storing the full Jacobian), **tesseroid (spherical-prism) forward modelling** for a curved Earth, and **first-order Tikhonov smoothness regularization** for stability. Applied to estimate the **South American Moho** from satellite gravity (GOCO5S) validated against seismological Moho depths. Published in *Geophysical Journal International* 208, 162–176. doi:10.1093/gji/ggw390.

First author **Leonardo Uieda** is the creator of the open-source [[wiki/entities/fatiando-a-terra]] project — the direct ancestor of Harmonica, recommended for this project's tooling.

## Key Points

- Target is the relief of the real Moho undulating around a reference (Normal Earth) Moho at depth `z_ref`; parametrized as a grid of juxtaposed tesseroids (see [[wiki/concepts/tesseroid-forward-modeling]]).
- Uses [[wiki/concepts/botts-method-gravity-inversion]]: the full Jacobian is replaced by a **diagonal** Bouguer-plate approximation `A = 2πGΔρ·I`, computed once → large speed gain over Gauss–Newton.
- Stabilized with [[wiki/concepts/regularized-interface-gravity-inversion]] (Tikhonov smoothness), solved as a constrained inverse problem via the goal function `Γ(p) = φ(p) + μ·θ(p)`.
- Sparse matrices for sensitivity `A` and roughness `R`; **~99.8 % of runtime is forward modelling**, the sparse linear solve is <0.1 %.
- Three [[wiki/concepts/gravity-inversion-hyperparameters]]: regularization `μ` (hold-out cross-validation), Moho density-contrast `Δρ`, and reference depth `z_ref` (validation against known Moho depths).
- Input data prepared via [[wiki/concepts/gravity-data-corrections]]: gravity disturbance → remove topo effect → Bouguer disturbance → remove sediment effect (CRUST1.0) → **sediment-free Bouguer disturbance**.
- South America result: estimated `μ = 1e-10` (little/no regularization), `z_ref = 35 km`, `Δρ = 400 kg/m³`. Moho >70 km under central Andes; 7.5–20 km oceanic; thinner (30–35 km) under Andean foreland, Chaco, and centres of Solimões/Amazonas/Paraná basins.
- Gravity–seismic discrepancies largest along the Andes (subducting Nazca plate not modelled) and in Amazonas/Paraná basins (Moho underestimated by up to 15 km → likely unmodelled high-density lower-crustal rocks). Such mismatches flag **crustal/mantle density anomalies unaccounted for in the corrections**.

## Method limitations (stated)

- Requires a **regular grid**; the model mesh is tied to the data grid.
- Works for **gravity disturbances only**, not gravity gradients.
- Smoothness regularization **cannot recover sharp Moho variations** (e.g. Andes); authors suggest sharpness-inducing alternatives (weighted smoothness, Cauchy-norm, entropic, total-variation, adaptive mixed).

## Data & software availability

- Satellite gravity: **GOCO5S** (Mayer-Guerr et al. 2015). Topography: **ETOPO1**. Sediments: **CRUST1.0** (Laske et al. 2013). Validation Moho: **Assumpção et al. (2013)** seismological compilation (937 points).
- Resulting South American Moho model: figshare `10.6084/m9.figshare.3987267`.
- Built on Tesseroids + Fatiando a Terra; uses matplotlib, SciPy, IPython, seaborn.

## Extracted Concepts

- [[wiki/concepts/tesseroid-forward-modeling]]
- [[wiki/concepts/botts-method-gravity-inversion]]
- [[wiki/concepts/regularized-interface-gravity-inversion]]
- [[wiki/concepts/gravity-inversion-hyperparameters]]
- [[wiki/concepts/gravity-data-corrections]]

## Extracted Entities

- [[wiki/entities/fatiando-a-terra]]

## Conflicts / Updates

- None yet (first source in the vault).

## Open Questions

- [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]]
