<!-- afk-research:managed v1 -->
# Bott's method for gravity inversion

---
title: "Bott's method for gravity inversion"
type: concept
status: active
created: 2026-07-28
updated: 2026-07-28
sources:
  - "[[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]"
tags:
  - gravity-inversion
  - methods
  - efficiency
---

## Summary

**Bott (1960)** is an efficient iterative method to estimate the depth of an interface (originally a sedimentary-basin basement) from gravity data on a regular grid. It updates the depth estimate each iteration by a correction derived from the inversion residuals, using a **Bouguer-plate approximation** of the relief's gravitational effect — so it needs only forward modelling, not the construction/solution of large linear systems.

## Key Points

- Correction per iteration: `Δp^k = (d⁰ − d(p^k)) / (2πGΔρ)`; iterate until residuals fall below the assumed noise level.
- Silva et al. (2014) recast Bott's method as a **special case of Gauss–Newton** by setting the Jacobian to the diagonal `A = 2πGΔρ·I` (identity scaled by the Bouguer-plate derivative). This **linearizes** the Jacobian and eliminates the cost of computing/storing the full dense `N×M` sensitivity matrix.
- Advantage: avoids the dense Jacobian and the equation-system solve → very low computational footprint.
- Disadvantage: plain Bott's method can be **unstable**; commonly countered by post-inversion smoothing (Silva et al. 2014) or, as in the source paper, by embedding it in a Tikhonov-regularized goal function.

## Links

- Combined with [[wiki/concepts/tesseroid-forward-modeling]] and [[wiki/concepts/regularized-interface-gravity-inversion]] in the source method.
- Source: [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]

## Open Questions

- How does the Bouguer-plate Jacobian approximation perform for a fore-arc basement with strong lateral density contrasts? See [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]].
