<!-- afk-research:managed v1 -->
# Tesseroid forward modeling

---
title: "Tesseroid forward modeling"
type: concept
status: active
created: 2026-07-28
updated: 2026-07-28
sources:
  - "[[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]"
tags:
  - forward-modeling
  - spherical-earth
  - gravity
---

## Summary

A **tesseroid** (spherical prism) is a mass element bounded by two meridians, two parallels, and two concentric spheres. Using tesseroids to compute gravitational effects respects **Earth curvature**, which matters for regional-to-global study areas where the planar (rectangular-prism) approximation is inadequate for depth-to-interface modelling.

## Key Points

- No closed-form solution exists for a tesseroid; its effect is computed **numerically**, typically by **Gauss–Legendre Quadrature (GLQ)** integration.
- GLQ suffers numerical instability when the computation point is close to the tesseroid; this is mitigated by the **adaptive discretization** scheme of Uieda et al. (2016), which subdivides tesseroids near the observation point.
- Observations at point P use a local north-oriented coordinate system; the tesseroid sits in a geocentric system (X, Y, Z).
- In interface inversion, the anomalous Moho is discretized into a grid of juxtaposed tesseroids whose thicknesses (depths `z_k`) are the parameters to estimate.

## Links

- Used by: [[wiki/concepts/regularized-interface-gravity-inversion]], [[wiki/concepts/botts-method-gravity-inversion]]
- Implemented in: [[wiki/entities/fatiando-a-terra]] (Tesseroids / Harmonica)
- Source: [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]

## Open Questions

- Is a spherical (tesseroid) approximation necessary for the Indonesian study areas, or does the regional extent allow a planar prism approach? See [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]].
