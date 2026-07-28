<!-- afk-research:managed v1 -->
# Fatiando a Terra

---
title: "Fatiando a Terra"
type: entity
status: active
created: 2026-07-28
updated: 2026-07-28
sources:
  - "[[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]"
tags:
  - software
  - dataset-tooling
  - python
---

## Summary

**Fatiando a Terra** is an open-source Python ecosystem for geophysical modelling and inversion, created by **Leonardo Uieda** (first author of the source paper). Its gravity/magnetics work moved into **Harmonica**, and the tesseroid forward modelling into **Boule/Harmonica** (originally the standalone *Tesseroids* code). It is the practical toolkit for reproducing this project's gravity workflow with public data.

## Why it matters here

- Directly implements [[wiki/concepts/tesseroid-forward-modeling]], gravity corrections, gridding, and forward/inverse modelling used in [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]].
- Recommended tooling for the FBT / Sumatra fore-arc gravity work (open-source, reproducible, spherical-Earth capable) alongside PyGMT, SimPEG, and pyshtools.
- The source paper's software lineage (Tesseroids + Fatiando) is the ancestor of the modern Harmonica package.

## Related Concepts

- [[wiki/concepts/tesseroid-forward-modeling]]
- [[wiki/concepts/gravity-data-corrections]]
- [[wiki/concepts/regularized-interface-gravity-inversion]]

## Related Sources

- [[wiki/sources/uieda-barbosa-2017-spherical-gravity-inversion]]

## Open Questions

- Does the current Harmonica release expose a Bott/tesseroid Moho-inversion equivalent to the source paper, or must it be reimplemented on top of its forward modelling? See [[wiki/questions/applying-spherical-gravity-inversion-to-indonesia]].
