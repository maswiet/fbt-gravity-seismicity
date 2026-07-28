<!-- afk-research:managed v1 -->
# Regularized interface gravity inversion

---
title: "Regularized interface gravity inversion"
type: concept
status: active
created: 2026-07-28
updated: 2026-07-28
sources:
  - "[[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]"
tags:
  - gravity-inversion
  - regularization
  - moho
---

## Summary

Estimating the relief of an interface separating two media (e.g. the Moho, or a sediment–basement contact) from gravity data is a **nonlinear, ill-posed** inverse problem. It is stabilized by **first-order Tikhonov smoothness regularization**, reformulated as a well-posed constrained problem minimizing a goal function that balances data misfit against solution roughness.

## Key Points

- Data-misfit: `φ(p) = [d⁰ − d(p)]ᵀ[d⁰ − d(p)]`. Roughness: `θ(p) = pᵀRᵀRp`, where `R` is a finite-difference matrix of first-order differences between adjacent tesseroid depths.
- Goal function: `Γ(p) = φ(p) + μ·θ(p)`, minimized with **Gauss–Newton**; `μ` is the regularization parameter (see [[wiki/concepts/gravity-inversion-hyperparameters]]).
- The source method fuses this Tikhonov formulation with [[wiki/concepts/botts-method-gravity-inversion]] (diagonal Jacobian) and [[wiki/concepts/tesseroid-forward-modeling]] (spherical forward model) → efficiency of Bott + stability of regularization.
- Sparse `A` and `R` make the linear algebra cheap; forward modelling dominates runtime.
- **Limitation:** smoothness regularization softens/blurs **sharp** interface variations (e.g. Moho step under the Andes). Sharpness-inducing regularizations (weighted smoothness, total variation, Cauchy-norm, entropic) are suggested alternatives.

## Evidence

- South American Moho recovered with acceptable data misfit at `μ = 1e-10` (nearly unregularized); smooth-Moho synthetic test recovered well except the shortest-wavelength (sharp) features.

## Links

- Depends on: [[wiki/concepts/tesseroid-forward-modeling]], [[wiki/concepts/botts-method-gravity-inversion]]
- Hyperparameters: [[wiki/concepts/gravity-inversion-hyperparameters]]
- Input prep: [[wiki/concepts/gravity-data-corrections]]
- Source: [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]

## Open Questions

- Which regularization (smoothness vs sharpness-inducing) suits a fore-arc basement with fault-bounded steps? See [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]].
