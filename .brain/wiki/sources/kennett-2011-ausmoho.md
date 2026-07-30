<!-- afk-research:managed v1 -->
# Kennett et al. (2011) — AusMoho: variation of Moho depth in Australia

---
title: "Kennett et al. (2011) — AusMoho"
type: source
status: active
created: 2026-07-29
updated: 2026-07-29
source_author: "B.L.N. Kennett; M. Salmon; E. Saygin; AusMoho Working Group"
source_created: 2011-08-15
source_url: "https://doi.org/10.1111/j.1365-246X.2011.05194.x"
raw: ""
tags:
  - moho
  - australia
  - seismic
  - validation
  - comparison
---

## Summary

AusMoho (GJI 187, 946–958) is a continent-wide compilation of Moho depth for Australia from refraction (>10,000 km), receiver functions (>150 sites) and full-crustal reflection (>11,000 km) data, interpolated to a 0.5° surface (weighted means; tension gridding). It is the reference seismic Moho model for the Australian plate and the natural cross-check for the SOUTHERN edge of our Indonesian gravity Moho, where the Australian continental margin (Arafura Shelf) underlies the region.

## Key values (northern Australia, bordering our study area)

- North Australian Craton / Arnhem Land (~130–137°E, −11 to −13°S): thick continental crust, **~35–40 km**.
- NW shelf / Timor Sea (~124–130°E): thinner, with a noted "Moho depression off the northwest coast" (~25–33 km).
- The far-northern edge of AusMoho is **poorly constrained** (sparse data; 250 km mask) — largely interpolation/extrapolation there.

## Comparison with our model (QUANTITATIVE, gridded)

We obtained the AusMoho2012 grid (`data/external/ausmoho/AusMoho2012.xyz`, lat lon depth, 0.5°, lat ≤ −10), extended our inversion domain south to −15°S (GGM 0.5°), and sampled our Moho at every AusMoho cell in the overlap:

- **Northern Australian mainland (−15..−11.5°S, N=369):** mean difference (ours − AusMoho) **−0.14 km**, std **4.84 km**, RMSE 4.84 km, **r = 0.86**. Near-zero bias + strong correlation between two *independent* methods (satellite-gravity inversion vs seismic compilation).
- **Full overlap incl. offshore Timor Sea (−15..−10°S, N=477):** mean +0.73 km, std 5.83 km, r = 0.76.
- Systematic deviations: (i) slight underestimation of the deepest (>40 km) cratonic crust (near-unregularized Bouguer inversion saturates); (ii) local over-thickening (~50 km) at the Timor–Banda collision front (real collisional thickening exaggerated by the single-Δρ assumption).
- Figure: `figures/moho/ausmoho_comparison.png`.
- Caveats: AusMoho's northernmost cells (−10 to −11.5°S, offshore) are low-confidence; Moho definitions differ slightly.

## Relevance

- Provides the previous-work comparison for the manuscript's southern boundary and independent support that the model is quantitatively reasonable at the Australian margin.
- See [[wiki/syntheses/moho-indonesia-replication-plan]] and the draft in `manuscript/`.

## Open Questions

- For a rigorous test: obtain the gridded AusMoho surface (Geoscience Australia / IRIS EMC) and compute a cell-by-cell difference in the 118–141°E, 9–11°S overlap.
