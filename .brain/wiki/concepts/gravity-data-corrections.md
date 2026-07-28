<!-- afk-research:managed v1 -->
# Gravity data corrections (to sediment-free Bouguer disturbance)

---
title: "Gravity data corrections (to sediment-free Bouguer disturbance)"
type: concept
status: active
created: 2026-07-28
updated: 2026-07-28
sources:
  - "[[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]"
tags:
  - gravity
  - data-processing
  - bouguer
---

## Summary

Before inverting for an interface, all gravitational effects **except** the target anomalous interface must be removed from the observed gravity. The source paper isolates the anomalous-Moho signal through a sequence of tesseroid-based corrections on a spherical Earth, ending at the **sediment-free Bouguer disturbance** used as inversion input.

## Correction sequence

1. **Gravity disturbance** `δ(P) = g(P) − γ(P)`: subtract Normal (ellipsoidal reference Earth) gravity `γ` computed at the same point (closed-form, Li & Götze 2001). Contains only effects anomalous w.r.t. the Normal Earth.
2. **Bouguer disturbance** `δ_bg(P) = δ(P) − g_topo(P)`: remove the modelled gravitational effect of topography + oceans (tesseroids; standard densities **2670 kg/m³** continents, **−1630 kg/m³** oceans relative to reference; or 1000-density seawater conventions).
3. **Sediment-free Bouguer disturbance**: subtract the modelled effect of sedimentary basins (e.g. from **CRUST1.0** upper/middle/lower sediment layers, each a tesseroid model). Assumes other crustal/mantle sources are negligible.

The remaining signal is attributed to the anomalous interface relief → the inversion input.

## Key Points

- Unmodelled crustal/mantle density anomalies (or an inaccurate sediment model) **bias** the inversion: a positive unmodelled density excess makes the observed disturbance larger → inversion produces a spuriously shallow interface. This explained gravity–seismic Moho mismatches in the Amazonas/Paraná basins.
- Corrections use [[wiki/concepts/tesseroid-forward-modeling]] for spherical-Earth accuracy.

## Links

- Feeds: [[wiki/concepts/regularized-interface-gravity-inversion]]
- Source: [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]

## Open Questions

- Which public sediment/topography models (CRUST1.0, ETOPO, DEMNAS) and satellite gravity (GOCO5S, XGM2019e, EGM2008) best fit Indonesian fore-arc/back-arc targets? See [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]].
