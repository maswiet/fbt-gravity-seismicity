# Moho Depth Variation Across Indonesia from Seismically Constrained Satellite Gravity

**Authors:** Muhammad Zuhdi¹, Sudarmaji¹, Ade Anggraini², Herlan Darmawan², Theodorus Permana², Wiwit Suryanto¹,²,\*

¹ Geophysics Laboratory, Department of Physics, Universitas Gadjah Mada, Sekip Utara PO BOX BLS 21, Yogyakarta 55281, Indonesia
² Seismology Research Group, Department of Physics, Universitas Gadjah Mada, Yogyakarta 55281, Indonesia
\* Corresponding author: Wiwit Suryanto (ws@ugm.ac.id)

**Status:** DRAFT for internal review — v0.2 (2026-07-30). Not for submission.

> Reviewer note: remaining placeholders in **[brackets]** — corresponding-author email, and the provenance/citation of the seismic-Moho compilation (`Depth_Moho.txt`) and the active-fault dataset ("Pak Wiwit"). All numbers below are from the current reproducible pipeline (`moho_indonesia/`).

---

## Abstract

The depth of the Mohorovičić discontinuity (Moho) is a first-order constraint on crustal structure, yet across the Indonesian archipelago it is known only unevenly, mostly from sparse seismic stations. We estimate the Moho of Indonesia (94°–141°E, 11°S–6°N) from satellite gravity by adapting the fast, regularized, spherical inversion of Uieda & Barbosa (2017): the anomalous Moho is discretized into tesseroids, forward-modelled on a spherical Earth, and inverted with Bott's method stabilized by first-order Tikhonov regularization. Gravity disturbances are derived from the satellite-only global model GOCO06S and corrected for topography/bathymetry with tesseroids. The three hyperparameters — regularization weight μ, density contrast Δρ, and reference depth z_ref — are estimated by hold-out cross-validation and by validation against a compilation of [N=105] receiver-function Moho depths. The preferred model (μ=10⁻¹⁰, z_ref=35 km, Δρ=500 kg m⁻³) fits the seismic Moho with a mean difference of +1.1 km and a standard deviation of 5.8 km, comparable to the original South American application (1.2 km, 6.8 km). As an external check, extending the domain south and comparing with the independent seismic AusMoho model over northern Australia yields near-zero bias (−0.1 km), a scatter of 4.8 km and a correlation of 0.86. Benchmarked at the same 105 stations, our independent model matches the seismically compiled CRUST1.0 (std 5.8 vs 5.3 km) despite twice-as-fine (0.5°) sampling, whereas the GOCE-derived GEMMA model is systematically 7.4 km too shallow (RMS 10.2 km) — evidence that existing global models are inadequate for Indonesia. The gravity Moho is thick (35–45 km) beneath the Sunda arc (Sumatra, Java), the Sulawesi–Banda arcs and the Papua highlands, and thin (10–20 km) beneath the marginal and oceanic basins. Estimated Moho depth co-varies with the volcanic arc, active faults and trenches, and the largest gravity–seismic discrepancies coincide with subduction/collision fronts where slab and crustal density anomalies are not modelled. We discuss resolution limits (the satellite gravity signal, not the model grid, controls resolution) and the limitations of land-biased validation.

**Keywords:** Moho; gravity inversion; tesseroids; Indonesia; satellite gravity; crustal structure

---

## 1. Introduction

The Mohorovičić discontinuity separates crust from mantle and is a primary target in studies of lithospheric structure, isostasy, and geodynamics. In tectonically complex regions such as Indonesia — where the Indo-Australian, Sunda, Philippine Sea and Pacific plates interact through subduction, collision and back-arc spreading — Moho depth varies strongly over short distances. Seismic methods (receiver functions, refraction, ambient-noise tomography) give the most direct estimates but are limited to the vicinity of stations, which in Indonesia are concentrated on land and along the volcanic arc (Zhang & Mooney, 2023).

Two global crustal models are commonly used where local constraints are absent. CRUST1.0 (Laske et al., 2013) is a 1°×1° compilation that, over Indonesia, is interpolated from sparse controls and inherits the sediment and crustal-type assumptions of its tiles; GEMMA (Reguzzoni & Sampietro, 2015; Rossi et al., 2022) is a 0.5° Moho inverted globally from GOCE gravity under a simplified two-layer density parameterization. Neither is tuned to Indonesian data, and both are too coarse to resolve the sharp arc/fore-arc crustal-thickness contrasts of the archipelago; as we show below (§4), GEMMA in particular is systematically ~7 km too shallow at Indonesian receiver-function stations. A dedicated, regionally calibrated gravity Moho is therefore warranted.

Gravity provides continuous, homogeneous coverage and is well suited to mapping the crust–mantle interface at regional scale, especially offshore where satellite altimetry and satellite gravity missions (GRACE, GOCE) give near-uniform data. Estimating an interface such as the Moho from gravity is a nonlinear, ill-posed inverse problem. Uieda & Barbosa (2017) introduced a computationally efficient solution in **spherical** coordinates that combines (i) Bott's (1960) iterative method, which avoids forming a dense Jacobian; (ii) tesseroid (spherical-prism) forward modelling, which respects Earth curvature at continental-to-global scale; and (iii) first-order Tikhonov regularization for stability. They applied it to the South American Moho using satellite gravity and validated it against seismic estimates.

Here we transfer that methodology, unchanged in principle, to the whole of Indonesia. Our objectives are to (1) produce a reproducible, public-data gravity Moho model of the Indonesian region; (2) calibrate and validate it against an independent compilation of seismic Moho depths; and (3) examine how the gravity Moho relates to the region's tectonic framework (trenches, active faults, volcanic arc). We deliberately keep the method identical to Uieda & Barbosa (2017) so that differences reflect the data and tectonic setting rather than the algorithm.

## 2. Data

**Satellite gravity.** We use the satellite-only global gravity model **GOCO06S** (Kvas et al., 2021), the successor of the GOCO5S model used by Uieda & Barbosa (2017), synthesised to spherical-harmonic degree/order 300. The gravity disturbance is evaluated on a regular grid at a constant height of 4 km above the WGS84 ellipsoid (above the highest topography), so that all forward computations share a common, singularity-free observation surface. For a higher-resolution variant we also use the altimetry-derived free-air gravity anomaly (`earth_faa`; Sandwell et al., 2014, via GMT) as a proxy for the disturbance.

**Topography/bathymetry.** Earth relief is taken from the GMT `earth_relief` grid (SRTM15+ / Tozer et al., 2019), resampled to the model grid.

**Seismic Moho (validation).** We use an independent compilation of **105 receiver-function (RF) Moho depths** at seismic stations spanning 96.3°–140.7°E, 10.2°S–5.2°N, provided as Supplementary Table S1 (station, longitude, latitude, depth). The depths range 20–40 km (mean 30.4, median 30 km); the distribution is 31 stations on Sumatra, 24 on Java and 50 in eastern Indonesia (Sulawesi, Banda arc, Papua), with none offshore (Figure 7a). Because the compilation draws on multiple RF studies with differing deconvolution schemes and 1-D reference velocity models, inter-study systematic differences of 2–5 km are expected and set a practical floor on the achievable fit; depths are reported below the ellipsoid, consistent with the modelled interface. The most comprehensive comparable regional compilation is Zhang & Mooney (2023) (H ≈ 24–38 km, Vp/Vs ≈ 1.79), consistent with the range used here. **[Confirm the per-station source references / network for `Depth_Moho.txt` to complete Table S1.]**

**Auxiliary data (interpretation).** Active faults (thrust, normal, strike-slip), fold axes and the Sunda–Banda trench are from **[Pak Wiwit dataset — provide citation]**; Holocene volcano locations are from the Smithsonian Global Volcanism Program (Global Volcanism Program, 2013). Sedimentary basins and sediment thickness are taken from CRUST1.0 (Laske et al., 2013) and, for interpretation, from the Indonesian sedimentary-basin maps of Darman & Yuliong (2020) and the Ministry of Energy and Mineral Resources (ESDM, 2022).

## 3. Methods

### 3.1 Gravity disturbance

The gravity disturbance at an observation point $P$ is the difference between the observed gravity $g(P)$ and the WGS84 normal (ellipsoidal) gravity $\gamma(P)$ evaluated at the same point,

$$\delta(P) = g(P) - \gamma(P). \tag{1}$$

$g(P)$ is synthesised from the satellite-only global gravity model GOCO06S to spherical-harmonic degree/order 300 on a regular grid at a constant height $h$ above the WGS84 ellipsoid; $\gamma(P)$ is computed with the closed-form Somigliana–Pizzetti formula. The disturbance contains only the effects of masses anomalous with respect to the reference ellipsoid. In the altimetry variant $\delta$ is approximated by the free-air gravity anomaly.

### 3.2 Forward modelling with tesseroids

All mass effects are computed on a spherical Earth using tesseroids (spherical prisms), which honour Earth curvature at regional scale. A tesseroid bounded by longitudes $[\lambda_1,\lambda_2]$, latitudes $[\phi_1,\phi_2]$ and radii $[r_1,r_2]$, of constant density $\rho$, produces at $P=(r_P,\phi_P,\lambda_P)$ the gravitational potential

$$V(P) = G\rho \int_{\lambda_1}^{\lambda_2}\!\!\int_{\phi_1}^{\phi_2}\!\!\int_{r_1}^{r_2} \frac{r^2\cos\phi}{\ell}\; dr\,d\phi\,d\lambda, \tag{2}$$

where $G$ is the gravitational constant and $\ell=\left(r_P^2+r^2-2r_Pr\cos\psi\right)^{1/2}$ is the distance from $P$ to the integration point, with $\cos\psi=\sin\phi_P\sin\phi+\cos\phi_P\cos\phi\cos(\lambda-\lambda_P)$. The datum modelled is the radial (vertical) component of the gravitational attraction,

$$g_z(P) = -\frac{\partial V}{\partial r_P} = G\rho \int_{\lambda_1}^{\lambda_2}\!\!\int_{\phi_1}^{\phi_2}\!\!\int_{r_1}^{r_2} \frac{(r_P-r\cos\psi)\,r^2\cos\phi}{\ell^{3}}\; dr\,d\phi\,d\lambda, \tag{3}$$

which has no analytical solution and is evaluated numerically by Gauss–Legendre Quadrature with the adaptive discretization of Uieda et al. (2016), as implemented in Harmonica (Fatiando a Terra).

The anomalous Moho relief is parameterised as $M$ juxtaposed tesseroids, one per grid cell, each spanning the radial gap between the reference (Normal-Earth) Moho at radius $R-z_{\mathrm{ref}}$ and the true Moho at radius $R-z_k$; the unknowns are the $M$ Moho depths $\mathbf{p}=(z_1,\dots,z_M)^{T}$. Following the sign convention of Uieda & Barbosa (2017, their Fig. 1), a cell whose Moho is deeper than the reference ($z_k>z_{\mathrm{ref}}$) is assigned density contrast $-\Delta\rho$ (crust replacing mantle: a mass deficit) and a shallower cell $+\Delta\rho$. The predicted gravity at the $N$ observation points is then the nonlinear forward map

$$d_i(\mathbf{p}) = f_i(\mathbf{p}) = \sum_{k=1}^{M} g_z^{(k)}(P_i;\,z_k),\qquad i=1,\dots,N. \tag{4}$$

### 3.3 Data corrections

The gravitational effect of topography and oceans, $g_{\text{topo}}$, is forward-modelled with tesseroids (continental density $2670\ \mathrm{kg\,m^{-3}}$; oceans as a water–rock contrast $\rho_w-\rho_c\approx-1640\ \mathrm{kg\,m^{-3}}$) and removed to give the Bouguer disturbance,

$$\delta_{bg}(P) = \delta(P) - g_{\text{topo}}(P). \tag{5}$$

Optionally the CRUST1.0 sediment effect $g_{\text{sed}}$ (three layers, each with contrast $\rho_{\text{sed}}-\rho_c$) is also removed, giving the sediment-free Bouguer disturbance $\delta_{sf}=\delta_{bg}-g_{\text{sed}}$. The corrected field, attributed to the anomalous Moho, is the inversion input $\mathbf{d}^{o}$. The full reduction chain is shown in Figure 2.

### 3.4 Inverse problem

We seek the depths $\mathbf{p}$ that reproduce $\mathbf{d}^{o}$ by minimising the data-misfit functional

$$\phi(\mathbf{p}) = \big[\mathbf{d}^{o}-\mathbf{d}(\mathbf{p})\big]^{T}\big[\mathbf{d}^{o}-\mathbf{d}(\mathbf{p})\big]. \tag{6}$$

Because the forward map (4) is nonlinear and estimating an interface from gravity is ill-posed, we impose first-order Tikhonov (smoothness) regularization

$$\theta(\mathbf{p}) = \mathbf{p}^{T}\mathbf{R}^{T}\mathbf{R}\,\mathbf{p}, \tag{7}$$

where $\mathbf{R}$ is the finite-difference operator of first differences between horizontally adjacent tesseroid depths, and minimise the goal function

$$\Gamma(\mathbf{p}) = \phi(\mathbf{p}) + \mu\,\theta(\mathbf{p}). \tag{8}$$

$\Gamma$ is minimised by the Gauss–Newton method: at iteration $k$ the parameter perturbation $\Delta\mathbf{p}^{k}$ solves

$$\big(\mathbf{A}^{k\,T}\mathbf{A}^{k} + \mu\,\mathbf{R}^{T}\mathbf{R}\big)\,\Delta\mathbf{p}^{k} = \mathbf{A}^{k\,T}\big[\mathbf{d}^{o}-\mathbf{d}(\mathbf{p}^{k})\big] - \mu\,\mathbf{R}^{T}\mathbf{R}\,\mathbf{p}^{k}, \tag{9}$$

where $\mathbf{A}^{k}$ is the $N\times M$ Jacobian (sensitivity) matrix, $A_{ij}=\partial f_i/\partial z_j$. Following Bott (1960), recast as a Gauss–Newton special case by Silva et al. (2014), the dense Jacobian is replaced by the diagonal Bouguer-plate approximation

$$\mathbf{A} = -2\pi G\,\Delta\rho\;\mathbf{I}, \tag{10}$$

the minus sign expressing that a deeper Moho lowers the gravity. With (10) the term $\mathbf{A}^{T}\mathbf{A}=(2\pi G\Delta\rho)^{2}\mathbf{I}$ is diagonal and constant, so (9) is a sparse, symmetric positive-definite system that is factorised once and back-substituted each iteration. The model is updated,

$$\mathbf{p}^{k+1} = \mathbf{p}^{k} + \Delta\mathbf{p}^{k}, \tag{11}$$

with each $z_k$ clipped to the physical range $3\text{–}70$ km, and the iteration is stopped when the change in RMS data misfit falls below the noise level. For $\mu=0$, equations (9)–(11) reduce to the classical Bott update $\Delta z_j = \big[d^{o}_j - d_j(\mathbf{p}^{k})\big]\big/(2\pi G\Delta\rho)$.

### 3.5 Hyperparameters

The three hyperparameters — regularization weight $\mu$, density contrast $\Delta\rho$, and reference depth $z_{\mathrm{ref}}$ — are estimated in two steps (Uieda & Barbosa 2017, §2.6): $\mu$ by hold-out cross-validation on the gravity data, then $(z_{\mathrm{ref}},\Delta\rho)$ by validation against the seismic Moho depths (§4).

### 3.6 Resolution tests

We invert on $0.5^{\circ}$ and $0.25^{\circ}$ grids with both the GOCO06S satellite gravity and the `earth_faa` altimetry field, to separate grid resolution from data resolution.

## 4. Results

**Calibrated hyperparameters.** Cross-validation selects μ = 10⁻¹⁰ (essentially unregularized, as in the original study). The (z_ref, Δρ) validation surface (Figure 6) has a **broad, flat minimum**: z_ref ≈ 30–40 km fits well over a wide range of Δρ. Critically, the seismic misfit **decreases monotonically with increasing Δρ** and does not turn over within a physical range — the calibration argmin runs away to unphysically high density contrasts (>600 kg m⁻³, RMS still falling). This reflects the well-known non-uniqueness of gravity inversion: Δρ trades off against z_ref and the Moho amplitude, and with near-zero regularization and simplified corrections Δρ also absorbs unmodelled effects (sediments, the subducting slab, the constant-height approximation). We therefore do **not** adopt the raw seismic minimum; instead we fix a **physically reasonable Δρ = 500 kg m⁻³** (a typical crust–mantle contrast, comparable to the 400 kg m⁻³ of Uieda & Barbosa 2017 for South America) with **z_ref = 35 km**. This choice is independently supported by the AusMoho comparison, which gives near-zero bias (−0.1 km; §5), whereas the runaway high-Δρ solutions degrade that independent agreement. Critically, the fit is only *weakly* sensitive to Δρ over the physical range: at z_ref = 35 km the seismic RMS is 6.2 km at Δρ = 400, 6.0 km at 450, 5.9 km at 500 and 5.8 km at 600 kg m⁻³ — the curve flattens above ~450 kg m⁻³ to <0.1 km per 50 kg m⁻³. Adopting Δρ = 500 (rather than 400) therefore degrades the fit by only 0.3 km. Δρ should thus be read as an *effective* contrast, not a tightly determined physical quantity. Bott's iteration converged in typically 15–20 steps, the RMS misfit decreasing monotonically to below the 0.15-km stopping tolerance.

**Moho model.** The preferred GOCO06S model at 0.5° yields Moho depths of ~7–59 km. The crust is thick (35–45 km) beneath the Sunda volcanic arc (Sumatra, Java), the Sulawesi and Banda arcs, and the Papuan highlands, and thin (10–20 km) beneath the deep marginal basins (e.g. Banda Sea, Celebes/Makassar) and the oceanic domains. The 35-km contour closely outlines the main arc/continental blocks (Figure 1).

**Validation.** The estimated Moho differs from the 105 seismic depths by a mean of **+1.1 km** and a standard deviation of **5.8 km** (GOCO06S, 0.5°), comparable to the original South American result (mean 1.2 km, std 6.8 km). Robust statistics agree: median +1.2 km, interquartile range 6.9 km, with 63% and 89% of stations within ±5 and ±10 km respectively (no outliers excluded). This scatter is comparable to the identical method in South America (6.8 km; Uieda & Barbosa, 2017) and to the seismically referenced CRUST1.0 at these same stations (5.3 km; Table 2); gravity Moho models routinely differ from seismic and from one another by 4–8 km (van der Meijde et al., 2013; Reguzzoni & Sampietro, 2015). The point correlation is modest (r = 0.28) for two reasons. First, the RF depths span only a narrow 20–40 km range and are spatially clustered, compressing the dynamic range available to the correlation coefficient. Second, and more physically, the model shows a resolution-driven **amplitude compression**: an ordinary-least-squares fit of estimated on seismic depth has a slope of only 0.20 (intercept 25 km; Figure 8), so the smooth ~67 km satellite-gravity field overestimates the thinnest crust and underestimates the thickest, while still tracking the mean trend (binned-mean r = 0.94). The grid-to-grid AusMoho comparison (§5), which compares like with like, is a fairer test and yields r = 0.86 — confirming that the low point-wise r largely reflects the test, not the model. The largest residuals cluster along the arcs and collision fronts (Figure 7b).

**Sediment correction.** Adding the CRUST1.0 sediment correction (sediment thickness 0–8.7 km, effect −3 to −191 mGal) does **not** improve the fit to the seismic Moho (mean −1.6 km, std 6.4 km). We attribute this to the land-biased validation: the seismic stations sit where CRUST1.0 sediments are thin, whereas the correction mainly reshapes offshore basins that the validation does not sample.

**Resolution.** Refining the grid from 0.5° to 0.25° with GOCO06S does not improve, and slightly degrades, the seismic fit (mean +3.2 km, std 8.0 km), because the satellite gravity signal does not support finer structure (at degree/order 300 the shortest resolved half-wavelength is ≈ 20,000/300 ≈ 67 km, i.e. ≈ 0.6°, so shorter wavelengths are unrecoverable from GOCO06S regardless of grid spacing) and the near-unregularized inversion overfits. Substituting the higher-resolution altimetry gravity at 0.25° recovers a near-zero bias (mean +0.9 km, std 6.9 km) and a cleaner, more detailed map, confirming that the resolution limit is set by the **gravity data**, not the model grid (Figure 2, Table 1).

**Table 1.** Difference between estimated and seismic Moho (N=105) by gravity source and grid.

| Gravity source | Grid | Mean (km) | Std (km) |
|---|---|---|---|
| GOCO06S (satellite) | 0.5° | +1.1 | **5.8** |
| Altimetry (earth_faa) | 0.5° | +1.4 | 6.0 |
| GOCO06S (satellite) | 0.25° | +3.2 | 8.0 |
| Altimetry (earth_faa) | 0.25° | +0.9 | 6.9 |

**Comparison with global reference models.** We benchmark the gravity Moho against the two global reference models most used in Indonesia — the seismically compiled CRUST1.0 (Laske et al., 2013) and the GOCE-derived GEMMA (Reguzzoni & Sampietro, 2015) — by sampling all three at the 105 RF stations (Table 2; Figures 8–9). Our model matches the seismic depths as well as CRUST1.0 (std 5.8 vs 5.3 km; 89% vs 94% within ±10 km), despite being derived independently from gravity alone and at twice the grid sampling — and notwithstanding that CRUST1.0 itself *incorporates* some of the same RF results as priors, giving it an intrinsic advantage at these very points. GEMMA, by contrast, is systematically 7.4 km too shallow (RMS 10.2 km, r = 0.08), with the largest deficits (15–24 km) at the fore-arc/island-arc transitions of southern Java and the Banda arc, where its coarse grid and global two-layer density model cannot capture the crustal thickening resolved by both the seismic stations and our inversion. Spatially (Figure 9), our model agrees with CRUST1.0 to within ±5 km across the continental interior and diverges (deeper) mainly along the Sunda–Java trench, where CRUST1.0 is weakly constrained; it is deeper than GEMMA almost everywhere. This benchmark substantiates the claim that existing global models are inadequate for Indonesia and that a regionally calibrated gravity Moho is a genuine improvement.

**Table 2.** Difference (model − seismic) at the 105 RF stations for this study and the two global reference models. IQR: interquartile range; ±5/±10: per cent of stations within ±5/±10 km.

| Model | Mean (km) | Median (km) | Std (km) | IQR (km) | RMS (km) | r | ±5 km | ±10 km |
|---|---|---|---|---|---|---|---|---|
| **This study** | +1.2 | +1.2 | **5.8** | 6.9 | **5.9** | 0.28 | 63% | 89% |
| CRUST1.0 | −1.3 | −1.2 | 5.3 | 7.5 | 5.4 | 0.36 | 66% | 94% |
| GEMMA | −7.4 | −6.5 | 7.1 | 9.5 | 10.2 | 0.08 | 36% | 64% |

## 5. Discussion

**Tectonic correlation.** The gravity Moho is spatially organized by the region's tectonics (Figures 3–4): thick crust follows the volcanic arc and the collision zones of Sulawesi, the Banda arc and Papua, while thin crust marks the oceanic marginal basins. Holocene volcanoes lie along the thick-crust arc; active thrust systems concentrate in eastern Indonesia (Papua, Sulawesi, Banda), and the Sumatran and Palu–Koro strike-slip systems bound arc segments.

**Gravity–seismic discrepancies.** As in Uieda & Barbosa (2017), the largest misfits occur where density anomalies unrelated to the Moho are not modelled — here, the subducting Sunda–Banda slabs and volcanic/collisional crustal bodies. These misfit patterns are themselves informative, flagging regions of anomalous crust/mantle density that warrant dedicated study.

**Limitations.** (1) *Validation is land-biased*: the seismic Moho compilation is station-based and mostly onshore, so it constrains the arc and continental crust well but cannot validate the oceanic/offshore Moho or the sediment correction. (2) *Resolution* is limited by the satellite gravity model; genuine 0.25° detail requires a higher-degree combined model (e.g. XGM2019e) or the altimetry field, and the added detail cannot be validated by the smooth station data. (3) The *sediment correction* had little benefit: the global CRUST1.0 model did not improve the fit, and a correction built from station receiver-function sediment thicknesses (Bahri, 2023) over-corrected — the western Moho, already in near-zero-bias agreement with the seismic estimates (mean +0.0 km) without any sediment correction, was pushed ~2 km too shallow. Because the receiver-function thicknesses are thin (mostly ~2 km) and point-sampled, they do not resolve the basin depocenters that the correction requires; an Indonesia-specific *basin-scale* sediment/depth-to-basement map (Hardy et al., 1997; Darman & Yuliong, 2020; ESDM, 2022) would be needed. This indicates that, at the validation points, sediments are a minor effect and are not the cause of the Δρ trade-off (§4). (4) The *single, uniform density contrast* is a simplification: a domain spanning oceanic, arc and continental crust would ideally use a Δρ that varies by tectonic domain, and the near-zero AusMoho bias at the continental margin suggests the effective value is close to correct there but may not be optimal beneath oceanic basins. (5) *Slab-gravity contamination*: because the diagonal Bouguer-plate Jacobian attributes all anomalous gravity to the Moho, the gravitational effect of the subducting Sunda–Banda slabs is not separated and can bias the estimated Moho downward near the trenches — consistent with the deeper-than-CRUST1.0 signature there (Figure 9b) and with the largest gravity–seismic residuals occurring at the subduction fronts. (6) *Uncertainty*: we do not provide a formal bootstrap/ensemble uncertainty map; instead the hyperparameter sensitivity (§4) bounds the systematic contribution (varying Δρ across 400–600 kg m⁻³ moves the seismic RMS by <0.5 km), while the 5.8-km validation scatter is an empirical error estimate at the stations. (7) *Offshore*, where continuous coverage is the model's main advantage, it is validated only indirectly (via AusMoho at the Australian margin); dedicated wide-angle refraction profiles such as Planert et al. (2010) at the Sunda–Banda transition would give direct offshore control in future work.

**Independent validation against AusMoho.** To test the model beyond the Indonesian receiver-function points used in calibration, we extended the inversion domain south to 15°S and compared with the independent seismic AusMoho model (Kennett et al., 2011; 0.5° grid) in the overlap zone. Over the northern Australian continental mainland (15°–11.5°S, N=369 AusMoho cells) our gravity Moho matches AusMoho with a mean difference of **−0.1 km**, a standard deviation of **4.7 km**, an RMSE of 4.7 km and a correlation of **r=0.86** (Figure 5). Including the offshore Timor Sea strip (15°–10°S, N=477) gives mean +0.7 km, std 5.4 km, r=0.79. Because AusMoho is derived entirely from seismic data (refraction, receiver functions, reflection) and is independent of our gravity inversion, this near-zero bias and strong correlation provide external confirmation that the method recovers absolute Moho depth, not merely relative variations. The largest deviations are (i) a slight underestimation of the deepest (>40 km) cratonic crust, where the near-unregularized Bouguer inversion saturates, and (ii) local over-thickening (up to ~50 km) at the Timor–Banda collision front, where crust is genuinely thickened by underthrusting of the Australian margin but the single-density-contrast assumption exaggerates it.

**Comparison with global reference models.** The station-level benchmark (§4, Table 2) shows that our independent gravity Moho is competitive with the seismically compiled CRUST1.0 and markedly better than the GOCE-derived GEMMA over Indonesia. GEMMA's ~7 km shallow bias is not a sign error — spot checks at continental stations give plausible GEMMA depths (26–41 km) and oceanic values (8–12 km), but at the sharp fore-arc/island-arc transitions (southern Java, Banda) GEMMA's 0.5° grid and simplified global density model return 15–20 km where receiver functions and our inversion both give ~35–40 km. This is a documented limitation of purely gravimetric global Moho models in tectonically complex margins and directly motivates a regional treatment. The strong agreement with CRUST1.0 in the continental interior, and the divergence localized to the trench (Figure 9b), also help separate genuine crustal structure from slab-related contamination (below).

## 6. Conclusions

We produced a reproducible, public-data gravity Moho model for the whole Indonesian region using the fast spherical Bott–Tikhonov tesseroid inversion of Uieda & Barbosa (2017). Calibrated against 105 seismic Moho depths, the model reproduces first-order crustal-thickness variations (thick arcs/continents, thin oceanic basins) and fits the seismic data to 5.8 km — comparable to the original application. Estimated Moho depth correlates with trenches, active faults and the volcanic arc, and the largest gravity–seismic residuals coincide with subduction/collision fronts. Resolution is limited by the satellite gravity data rather than the model grid, and land-biased seismic control precludes validation of the offshore Moho. The model provides a regional starting framework and highlights where dedicated seismic and higher-resolution gravity work would be most valuable.

## Data and code availability

All inversion, calibration and plotting code is openly available at **https://github.com/maswiet/fbt-gravity-seismicity** (`moho_indonesia/`), and the final Moho grid and the 105-point RF compilation (Supplementary Table S1) will be archived with a citable DOI on Zenodo on acceptance **[insert DOI]**. Input data are public: GOCO06S (ICGEM), GMT `earth_relief`/`earth_faa` (SRTM15+ / Sandwell et al.), CRUST1.0, GEMMA (http://gocedata.como.polimi.it), and the Smithsonian GVP volcano list. The seismic Moho compilation, the active-fault dataset and the AusMoho grid are third-party and redistributed subject to their original licences **[specify/authorise sources]**.

## References (to complete/format for target journal)

- Bahri, S. (2023). Sediment thickness and Moho depth of western Indonesia from receiver-function inversion [MSc thesis]. Universitas Gadjah Mada, Yogyakarta. **[confirm title/year]**
- Bott, M.H.P. (1960). The use of rapid digital computing methods for direct gravity interpretation of sedimentary basins. *Geophys. J. Int.*, 3, 63–67.
- Darman, H. & Yuliong, D.B.A. (2020). Sedimentary Basins of Indonesia: Outline and Thickness Variation Understanding. *Berita Sedimentologi*, 45, 39–52.
- ESDM (2022). *Peta Cekungan Sedimen Indonesia / Sedimentary Basin Map of Indonesia* (1:5,000,000). Kementerian ESDM, Indonesia.
- Global Volcanism Program (2013). *Volcanoes of the World* (database). Smithsonian Institution.
- Hardy, L.R., Muchsin, S., Ichram, L.O., Samuel, L. & Purnomo, E. (1997). Application of the Petroleum System Concept to Reconnaissance Assessments of Mature and Emerging Producing Basins, with Examples from Indonesia. *Proc. Int. Conf. Petroleum Systems of SE Asia and Australasia*, IPA, Jakarta.
- Kvas, A., et al. (2021). GOCO06s – a satellite-only global gravity field model. *Earth Syst. Sci. Data*, 13, 99–118.
- Laske, G., Masters, G., Ma, Z. & Pasyanos, M. (2013). Update on CRUST1.0. *EGU Gen. Assembly*, EGU2013-2658.
- Planert, L., Kopp, H., Lüschen, E., et al. (2010). Lower plate structure and upper plate deformational segmentation at the Sunda-Banda arc transition, offshore Indonesia. *J. Geophys. Res.*, 115, B08107.
- Reguzzoni, M. & Sampietro, D. (2015). GEMMA: An Earth crustal model based on GOCE satellite data. *Int. J. Appl. Earth Obs. Geoinf.*, 35, 31–43.
- Rossi, L., Reguzzoni, M., Sampietro, D. & Sansò, F. (2022). Global Moho gravity inversion from GOCE data: updates and convergence assessment of the GEMMA model algorithm. *Remote Sens.*, 14, 5646.
- Sandwell, D.T., Müller, R.D., Smith, W.H.F., Garcia, E. & Francis, R. (2014). New global marine gravity model from CryoSat-2 and Jason-1. *Science*, 346, 65–67.
- Silva, J.B.C., Santos, D.F. & Gomes, K.P. (2014). Fast gravity inversion of basement relief. *Geophysics*, 79, G79–G91.
- Tozer, B., et al. (2019). Global bathymetry and topography at 15 arc sec: SRTM15+. *Earth Space Sci.*, 6, 1847–1864.
- Uieda, L. & Barbosa, V.C.F. (2017). Fast nonlinear gravity inversion in spherical coordinates with application to the South American Moho. *Geophys. J. Int.*, 208, 162–176.
- Uieda, L., Barbosa, V.C.F. & Braitenberg, C. (2016). Tesseroids: forward-modeling gravitational fields in spherical coordinates. *Geophysics*, 81, F41–F48.
- Zhang, X. & Mooney, W.D. (2023). Crustal structure of Indonesia and surrounding regions from receiver functions. *Tectonophysics*, 862, 230033.
- **[Add: seismic-Moho compilation reference; active-fault dataset reference; regional tectonics (e.g. Hall, 2002); Bird (2003) plate boundaries; prior Indonesian Moho studies.]**

## Figures (from `figures/moho/`)

1. **`moho_full_clean.png`** — Estimated Moho depth of Indonesia, with seismic Moho stations and depth contours (35-km contour highlighted).
1b. **`processing_chain.png`** (≡ U&B Fig. 8) — the gravity data-reduction chain: (a) gravity disturbance, (b) topography/bathymetry, (c) topographic effect, (d) Bouguer disturbance, (e) CRUST1.0 sediment effect, (f) sediment-free Bouguer disturbance (inversion input).
2. **`validation_seismic.png`** — Moho residual (estimated − seismic) at the 105 Indonesian stations, map and histogram (mean +1.2 km, std 5.8 km). Resolution/source summary in Table 1.
3. **`moho_west.png`** — Western Indonesia (94°–120°E): Moho with trench, active faults, folds and Holocene volcanoes.
4. **`moho_east.png`** — Eastern Indonesia (115°–141°E): as Figure 3, showing the Sulawesi–Banda–Papua collision belt.
5. **`ausmoho_comparison.png`** — Independent validation against AusMoho (Kennett et al., 2011): scatter of our vs AusMoho depth (coloured by latitude) and histogram of differences over the northern-Australia overlap.
6. **`hyperparameters.png`** — Hyperparameter diagnostics: μ hold-out cross-validation curve and the (z_ref, Δρ) validation-MSE surface (minimum at μ=10⁻¹⁰, z_ref=35 km, Δρ=500 kg m⁻³).
7. **`compare_global_models.png`** — (a) the 105 RF validation stations coloured by seismic depth (dense on Sumatra/Java, sparse in the east, absent offshore); (b) difference between this study and CRUST1.0 (agreement within ±5 km inland, deeper only along the Sunda–Java trench); (c) difference between this study and GEMMA (our model 5–10 km deeper almost everywhere).
8. **`scatter_vandermeijde.png`** — Depth–depth comparison (van der Meijde 2013 style): open circles vs the 1:1 line with ±6 km (black) and ±12 km (red) deviation bands; insets give bias, RMS, % within ±6/±12 km and slope. **Top row (vs the 105 seismic depths):** (a) this study, (b) CRUST1.0, (c) GEMMA. **Bottom row (model vs model over the grid, N=817):** (d) this study vs CRUST1.0, (e) this study vs GEMMA, (f) GEMMA vs CRUST1.0. Against point seismic, this study (slope 0.20) and CRUST1.0 (slope 0.23) show the *same* amplitude compression — evidence it stems from the reference data/scale mismatch, not our method. Grid-to-grid, this study tracks CRUST1.0 (slope 0.78) and shares GEMMA's spatial pattern (slope 0.93) but GEMMA is ~8 km too shallow (bias +7.7 km). [Also available: `scatter_vs_seismic.png`, the single-panel overlay with regression line and binned means.]

---

### Author checklist before submission
- [ ] Fill author names, affiliations, corresponding email.
- [ ] Cite the seismic-Moho compilation and confirm its depth datum (sea level vs ellipsoid).
- [ ] Obtain permission/citation for the active-fault dataset ("Pak Wiwit").
- [ ] Add a Previous-Work comparison (CRUST1.0/GEMMA/RF/ANT Moho for Indonesia).
- [ ] Choose the target journal and reformat references accordingly.
- [ ] Decide the "final" model to feature (GOCO06S 0.5° for best validation vs altimetry 0.25° for detail).
- [ ] Consider adding: joint gravity–magnetic, an Indonesia-specific sediment prior, and offshore Moho constraints.
