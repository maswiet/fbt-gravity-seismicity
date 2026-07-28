<!-- afk-research:managed v1 -->
# Gravity inversion hyperparameters (μ, Δρ, z_ref)

---
title: "Gravity inversion hyperparameters (μ, Δρ, z_ref)"
type: concept
status: active
created: 2026-07-28
updated: 2026-07-28
sources:
  - "[[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]"
tags:
  - gravity-inversion
  - cross-validation
  - hyperparameters
---

## Summary

Interface gravity inversion has three quantities that control the result but are not solved for directly. Estimating them well is essential and is done with a **two-step validation** strategy rather than manual tuning.

## The three hyperparameters

- **μ — regularization parameter:** balances data misfit vs solution smoothness. Estimated by **hold-out cross-validation**: split data into training/testing grids, invert on training, score prediction Mean Square Error (MSE) on testing across a range of `μ` (log-spaced), pick the MSE minimum. (Alternative: L-curve, GCV.)
- **Δρ — density contrast** across the interface (Moho or basement).
- **z_ref — reference depth** of the Normal-Earth interface (the constant depth the relief undulates around).

## Estimation workflow (two steps)

1. Fix `z_ref`, `Δρ`; run **cross-validation** to find optimal `μ`. (Finding: optimal `μ` was insensitive to the particular `z_ref`, `Δρ` used.)
2. Use that `μ`; run a **second validation against known interface depths** (e.g. seismological Moho points) over a grid of `(z_ref, Δρ)` to pick the pair minimizing MSE vs the reference depths.

## Evidence

- South America: `μ ≈ 1e-10` (near-zero regularization needed), `z_ref = 35 km`, `Δρ = 400 kg/m³`. The `(z_ref, Δρ)` minimum was less well-defined for real data than for the synthetic CRUST1.0 test — expected, since real `Δρ` is not homogeneous.

## Links

- Part of: [[wiki/concepts/regularized-interface-gravity-inversion]]
- Source: [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]

## Open Questions

- What independent depth constraints (well tops, seismic, receiver-function Moho) are available to validate `z_ref`/`Δρ` for Indonesian targets? See [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]].
