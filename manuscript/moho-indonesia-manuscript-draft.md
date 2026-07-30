# The Moho of Indonesia from Satellite Gravity: a fast spherical Bott–Tikhonov inversion validated against seismic estimates

**Authors:** [PhD Student Name]¹, [Advisor Name]¹ · **Affiliation:** ¹[Department / University]
**Corresponding author:** [email]
**Status:** DRAFT for internal review — v0.1 (2026-07-29). Not for submission.

> Reviewer note: placeholders in **[brackets]** need author input — names, affiliations, and the provenance/citation of the seismic-Moho compilation (`Depth_Moho.txt`) and the active-fault dataset ("Pak Wiwit"). All numbers below are from the current reproducible pipeline (`moho_indonesia/`).

---

## Abstract

The depth of the Mohorovičić discontinuity (Moho) is a first-order constraint on crustal structure, yet across the Indonesian archipelago it is known only unevenly, mostly from sparse seismic stations. We estimate the Moho of Indonesia (94°–141°E, 11°S–6°N) from satellite gravity by adapting the fast, regularized, spherical inversion of Uieda & Barbosa (2017): the anomalous Moho is discretized into tesseroids, forward-modelled on a spherical Earth, and inverted with Bott's method stabilized by first-order Tikhonov regularization. Gravity disturbances are derived from the satellite-only global model GOCO06S and corrected for topography/bathymetry with tesseroids. The three hyperparameters — regularization weight μ, density contrast Δρ, and reference depth z_ref — are estimated by hold-out cross-validation and by validation against a compilation of [N=105] receiver-function Moho depths. The preferred model (μ=10⁻¹⁰, z_ref=35 km, Δρ=500 kg m⁻³) fits the seismic Moho with a mean difference of +1.1 km and a standard deviation of 5.8 km, comparable to the original South American application (1.2 km, 6.8 km). The gravity Moho is thick (35–45 km) beneath the Sunda arc (Sumatra, Java), the Sulawesi–Banda arcs and the Papua highlands, and thin (10–20 km) beneath the marginal and oceanic basins. Estimated Moho depth co-varies with the volcanic arc, active faults and trenches, and the largest gravity–seismic discrepancies coincide with subduction/collision fronts where slab and crustal density anomalies are not modelled. We discuss resolution limits (the satellite gravity signal, not the model grid, controls resolution) and the limitations of land-biased validation.

**Keywords:** Moho; gravity inversion; tesseroids; Indonesia; satellite gravity; crustal structure

---

## 1. Introduction

The Mohorovičić discontinuity separates crust from mantle and is a primary target in studies of lithospheric structure, isostasy, and geodynamics. In tectonically complex regions such as Indonesia — where the Indo-Australian, Sunda, Philippine Sea and Pacific plates interact through subduction, collision and back-arc spreading — Moho depth varies strongly over short distances. Seismic methods (receiver functions, refraction, ambient-noise tomography) give the most direct estimates but are limited to the vicinity of stations, which in Indonesia are concentrated on land and along the volcanic arc.

Gravity provides continuous, homogeneous coverage and is well suited to mapping the crust–mantle interface at regional scale, especially offshore where satellite altimetry and satellite gravity missions (GRACE, GOCE) give near-uniform data. Estimating an interface such as the Moho from gravity is a nonlinear, ill-posed inverse problem. Uieda & Barbosa (2017) introduced a computationally efficient solution in **spherical** coordinates that combines (i) Bott's (1960) iterative method, which avoids forming a dense Jacobian; (ii) tesseroid (spherical-prism) forward modelling, which respects Earth curvature at continental-to-global scale; and (iii) first-order Tikhonov regularization for stability. They applied it to the South American Moho using satellite gravity and validated it against seismic estimates.

Here we transfer that methodology, unchanged in principle, to the whole of Indonesia. Our objectives are to (1) produce a reproducible, public-data gravity Moho model of the Indonesian region; (2) calibrate and validate it against an independent compilation of seismic Moho depths; and (3) examine how the gravity Moho relates to the region's tectonic framework (trenches, active faults, volcanic arc). We deliberately keep the method identical to Uieda & Barbosa (2017) so that differences reflect the data and tectonic setting rather than the algorithm.

## 2. Data

**Satellite gravity.** We use the satellite-only global gravity model **GOCO06S** (Kvas et al., 2021), the successor of the GOCO5S model used by Uieda & Barbosa (2017), synthesised to spherical-harmonic degree/order 300. The gravity disturbance is evaluated on a regular grid at a constant height of 4 km above the WGS84 ellipsoid (above the highest topography), so that all forward computations share a common, singularity-free observation surface. For a higher-resolution variant we also use the altimetry-derived free-air gravity anomaly (`earth_faa`; Sandwell et al., 2014, via GMT) as a proxy for the disturbance.

**Topography/bathymetry.** Earth relief is taken from the GMT `earth_relief` grid (SRTM15+ / Tozer et al., 2019), resampled to the model grid.

**Seismic Moho (validation).** An independent compilation of **[105] receiver-function Moho depths** at seismic stations spanning 96°–141°E, 10°S–5°N (depths 20–40 km) is used to calibrate z_ref and Δρ and to assess the model. **[Cite source of `Depth_Moho.txt` — IA/GEOFON/BMKG network; provide reference and depth datum.]**

**Auxiliary data (interpretation).** Active faults (thrust, normal, strike-slip), fold axes and the Sunda–Banda trench are from **[Pak Wiwit dataset — provide citation]**; Holocene volcano locations are from the Smithsonian Global Volcanism Program (Global Volcanism Program, 2013). Sedimentary basins and sediment thickness are taken from CRUST1.0 (Laske et al., 2013) and, for interpretation, from the Indonesian sedimentary-basin maps of Darman & Yuliong (2020) and the Ministry of Energy and Mineral Resources (ESDM, 2022).

## 3. Methods

**Gravity disturbance.** The gravity disturbance δ = g − γ is obtained by removing WGS84 normal gravity γ from the synthesised GOCO06S gravity at each grid point (or, in the altimetry variant, taken directly as the free-air anomaly).

**Topographic correction.** The gravitational effect of topography and oceans is forward-modelled with tesseroids (continental density 2670 kg m⁻³; oceans as a water–rock contrast of −1640 kg m⁻³) and subtracted from the disturbance to give the Bouguer disturbance. An optional sediment correction removes the tesseroid effect of the three CRUST1.0 sediment layers, yielding the sediment-free Bouguer disturbance that is the inversion input.

**Inversion.** The anomalous Moho is parameterised as a grid of juxtaposed tesseroids whose depths are the unknowns. We minimise the regularized goal function Γ(p) = φ(p) + μ·θ(p), where φ is the data misfit and θ = pᵀRᵀRp is a first-order roughness penalty. Following Bott's method as recast by Silva et al. (2014), the Jacobian is approximated by the diagonal Bouguer-plate value A = 2πGΔρ (with sign set so that a deeper Moho produces a negative anomaly), reducing each Gauss–Newton step to a sparse linear solve. Tesseroid effects are computed with the adaptive scheme of Uieda et al. (2016) as implemented in Harmonica (Fatiando a Terra). Moho depths are constrained to a physical range (3–70 km) each iteration.

**Hyperparameters.** Following Uieda & Barbosa (2017, §2.6), μ is chosen by hold-out cross-validation on the gravity data, and (z_ref, Δρ) by validation against the seismic Moho depths.

**Resolution tests.** We invert on 0.5° and 0.25° grids and with both the GOCO06S (satellite) and altimetry (`earth_faa`) gravity sources, to separate grid resolution from data resolution.

## 4. Results

**Calibrated hyperparameters.** Cross-validation selects μ = 10⁻¹⁰ (essentially unregularized, as in the original study), and validation against the seismic Moho selects **z_ref = 35 km** and **Δρ = 500 kg m⁻³**.

**Moho model.** The preferred GOCO06S model at 0.5° yields Moho depths of ~7–59 km. The crust is thick (35–45 km) beneath the Sunda volcanic arc (Sumatra, Java), the Sulawesi and Banda arcs, and the Papuan highlands, and thin (10–20 km) beneath the deep marginal basins (e.g. Banda Sea, Celebes/Makassar) and the oceanic domains. The 35-km contour closely outlines the main arc/continental blocks (Figure 1).

**Validation.** The estimated Moho differs from the 105 seismic depths by a mean of **+1.1 km** and a standard deviation of **5.8 km** (GOCO06S, 0.5°), comparable to the original South American result (mean 1.2 km, std 6.8 km). The largest residuals cluster along the arcs and collision fronts.

**Sediment correction.** Adding the CRUST1.0 sediment correction (sediment thickness 0–8.7 km, effect −3 to −191 mGal) does **not** improve the fit to the seismic Moho (mean −1.6 km, std 6.4 km). We attribute this to the land-biased validation: the seismic stations sit where CRUST1.0 sediments are thin, whereas the correction mainly reshapes offshore basins that the validation does not sample.

**Resolution.** Refining the grid from 0.5° to 0.25° with GOCO06S does not improve, and slightly degrades, the seismic fit (mean +3.2 km, std 8.0 km), because the satellite gravity signal (≈0.5°, d/o 300) does not support finer structure and the near-unregularized inversion overfits. Substituting the higher-resolution altimetry gravity at 0.25° recovers a near-zero bias (mean +0.9 km, std 6.9 km) and a cleaner, more detailed map, confirming that the resolution limit is set by the **gravity data**, not the model grid (Figure 2, Table 1).

**Table 1.** Difference between estimated and seismic Moho (N=105) by gravity source and grid.

| Gravity source | Grid | Mean (km) | Std (km) |
|---|---|---|---|
| GOCO06S (satellite) | 0.5° | +1.1 | **5.8** |
| Altimetry (earth_faa) | 0.5° | +1.4 | 6.0 |
| GOCO06S (satellite) | 0.25° | +3.2 | 8.0 |
| Altimetry (earth_faa) | 0.25° | +0.9 | 6.9 |

## 5. Discussion

**Tectonic correlation.** The gravity Moho is spatially organized by the region's tectonics (Figures 3–4): thick crust follows the volcanic arc and the collision zones of Sulawesi, the Banda arc and Papua, while thin crust marks the oceanic marginal basins. Holocene volcanoes lie along the thick-crust arc; active thrust systems concentrate in eastern Indonesia (Papua, Sulawesi, Banda), and the Sumatran and Palu–Koro strike-slip systems bound arc segments.

**Gravity–seismic discrepancies.** As in Uieda & Barbosa (2017), the largest misfits occur where density anomalies unrelated to the Moho are not modelled — here, the subducting Sunda–Banda slabs and volcanic/collisional crustal bodies. These misfit patterns are themselves informative, flagging regions of anomalous crust/mantle density that warrant dedicated study.

**Limitations.** (1) *Validation is land-biased*: the seismic Moho compilation is station-based and mostly onshore, so it constrains the arc and continental crust well but cannot validate the oceanic/offshore Moho or the sediment correction. (2) *Resolution* is limited by the satellite gravity model; genuine 0.25° detail requires a higher-degree combined model (e.g. XGM2019e) or the altimetry field, and the added detail cannot be validated by the smooth station data. (3) The *sediment correction* used a global 1°×1° model (CRUST1.0); an Indonesia-specific sediment/depth-to-basement map (Darman & Yuliong, 2020; ESDM, 2022) may perform better. (4) The reference height, single density contrast and coarse hyperparameter search are simplifications inherited from the method.

**Comparison with previous work.** At the southern boundary, our model can be compared with the independent seismic AusMoho compilation (Kennett et al., 2011). Where our region overlies the Australian continental margin (Arafura Shelf, Arnhem-Land approach; ~132°–140°E, 10°–11°S), our gravity Moho (~33–37 km) agrees with AusMoho's northern continental crust (~35–40 km) to within a few kilometres — encouraging agreement between two independent methods across the plate boundary. The main difference is at the Timor–Banda collision front (~124°–126°E), where our model gives markedly thicker crust (39–50 km), consistent with collisional thickening of the underthrusting Australian margin (a feature outside AusMoho's coverage; the ~50 km value may be slightly overestimated by the arc-thickening tendency of the method). Both models are least constrained at their shared edge — our non-padded southern row and AusMoho's sparsely sampled far north. [Add further comparison to CRUST1.0/GEMMA and Indonesian receiver-function / ambient-noise studies once collated.]

## 6. Conclusions

We produced a reproducible, public-data gravity Moho model for the whole Indonesian region using the fast spherical Bott–Tikhonov tesseroid inversion of Uieda & Barbosa (2017). Calibrated against 105 seismic Moho depths, the model reproduces first-order crustal-thickness variations (thick arcs/continents, thin oceanic basins) and fits the seismic data to 5.8 km — comparable to the original application. Estimated Moho depth correlates with trenches, active faults and the volcanic arc, and the largest gravity–seismic residuals coincide with subduction/collision fronts. Resolution is limited by the satellite gravity data rather than the model grid, and land-biased seismic control precludes validation of the offshore Moho. The model provides a regional starting framework and highlights where dedicated seismic and higher-resolution gravity work would be most valuable.

## Data and code availability

All code and processing are openly available at **https://github.com/maswiet/fbt-gravity-seismicity** (`moho_indonesia/`). Input data are public: GOCO06S (ICGEM), GMT `earth_relief`/`earth_faa`, CRUST1.0, and the Smithsonian GVP volcano list. The seismic Moho compilation and the active-fault dataset are third-party and available from **[sources — to be specified/authorised]**.

## References (to complete/format for target journal)

- Bott, M.H.P. (1960). The use of rapid digital computing methods for direct gravity interpretation of sedimentary basins. *Geophys. J. Int.*, 3, 63–67.
- Darman, H. & Yuliong, D.B.A. (2020). Sedimentary Basins of Indonesia: Outline and Thickness Variation Understanding. *Berita Sedimentologi*, 45, 39–52.
- ESDM (2022). *Peta Cekungan Sedimen Indonesia / Sedimentary Basin Map of Indonesia* (1:5,000,000). Kementerian ESDM, Indonesia.
- Global Volcanism Program (2013). *Volcanoes of the World* (database). Smithsonian Institution.
- Kvas, A., et al. (2021). GOCO06s – a satellite-only global gravity field model. *Earth Syst. Sci. Data*, 13, 99–118.
- Laske, G., Masters, G., Ma, Z. & Pasyanos, M. (2013). Update on CRUST1.0. *EGU Gen. Assembly*, EGU2013-2658.
- Sandwell, D.T., Müller, R.D., Smith, W.H.F., Garcia, E. & Francis, R. (2014). New global marine gravity model from CryoSat-2 and Jason-1. *Science*, 346, 65–67.
- Silva, J.B.C., Santos, D.F. & Gomes, K.P. (2014). Fast gravity inversion of basement relief. *Geophysics*, 79, G79–G91.
- Tozer, B., et al. (2019). Global bathymetry and topography at 15 arc sec: SRTM15+. *Earth Space Sci.*, 6, 1847–1864.
- Uieda, L. & Barbosa, V.C.F. (2017). Fast nonlinear gravity inversion in spherical coordinates with application to the South American Moho. *Geophys. J. Int.*, 208, 162–176.
- Uieda, L., Barbosa, V.C.F. & Braitenberg, C. (2016). Tesseroids: forward-modeling gravitational fields in spherical coordinates. *Geophysics*, 81, F41–F48.
- **[Add: seismic-Moho compilation reference; active-fault dataset reference; regional tectonics (e.g. Hall, 2002); Bird (2003) plate boundaries; prior Indonesian Moho studies.]**

## Figures (from `figures/moho/`)

1. **`moho_full_clean.png`** — Estimated Moho depth of Indonesia (0.25°), with seismic Moho stations and depth contours (35-km contour highlighted).
2. Resolution/validation summary (Table 1) — difference-vs-seismic maps and histograms (`real_difference_from_seismic.png`).
3. **`moho_west.png`** — Western Indonesia (94°–120°E): Moho with trench, active faults, folds and Holocene volcanoes.
4. **`moho_east.png`** — Eastern Indonesia (115°–141°E): as Figure 3, showing the Sulawesi–Banda–Papua collision belt.
5. Hyperparameter diagnostics (cross-validation curve for μ; validation surface for z_ref, Δρ).

---

### Author checklist before submission
- [ ] Fill author names, affiliations, corresponding email.
- [ ] Cite the seismic-Moho compilation and confirm its depth datum (sea level vs ellipsoid).
- [ ] Obtain permission/citation for the active-fault dataset ("Pak Wiwit").
- [ ] Add a Previous-Work comparison (CRUST1.0/GEMMA/RF/ANT Moho for Indonesia).
- [ ] Choose the target journal and reformat references accordingly.
- [ ] Decide the "final" model to feature (GOCO06S 0.5° for best validation vs altimetry 0.25° for detail).
- [ ] Consider adding: joint gravity–magnetic, an Indonesia-specific sediment prior, and offshore Moho constraints.
