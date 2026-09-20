"""
3-D gravity inversion for the Central Java sediment-basement relief following
Uieda & Barbosa (2017, GJI 208, 162-176) — "Fast nonlinear gravity inversion in
spherical coordinates" — adapted from the Moho to the sediment/basement interface.

Method (faithful to the paper):
  * the anomalous sediment layer is discretised into a grid of TESSEROIDS
    (spherical prisms), top at sea level, bottom at the basement depth b(x,y);
  * forward modelling uses harmonica.tesseroid_layer (GLQ, adaptive) — the same
    Fatiando/Tesseroids machinery used by Uieda;
  * the basement relief is estimated with the regularised Bott scheme, eq. 13:
        (A^2 I + mu R^T R) dp = A r - mu R^T R p,   A = 2*pi*G*drho (Bouguer-plate
    diagonal Jacobian, eq. 15), R = first-difference smoothness operator (eq. 9);
  * the density contrast drho is a hyperparameter that gravity ALONE cannot fix
    (sec. 2.6.2); we estimate it from KNOWN depths at points — here the receiver-
    function sediment thickness — exactly the role Uieda assigns to seismology.

Then we COMPARE the gravity-derived 3-D sediment thickness with the RF depths.

Outputs (figures/rf_java/):
  cj_uieda_fit.png             observed vs predicted gravity + residuals (coastline)
  cj_uieda_vs_rf.png           3-D sediment model, drho calibration, inverted-vs-RF
  cj_uieda_density_section.png representative basin density cross-section (VE-labelled)
  data/processed/rf_java/sediment_uieda3d.nc

Run (fbt env):  python rf_gravity_java/invert_uieda3d.py
"""
from __future__ import annotations
import sys, pathlib
import numpy as np, pandas as pd, xarray as xr
import verde as vd, boule, harmonica as hm
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator as RGI
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.stats import pearsonr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C
from _coast import add_coast

D = C.DATA_PROCESSED
FIG = C.FIGURES
R_E = boule.WGS84.mean_radius
TWO_PI_G = 2 * np.pi * 6.674e-11 * 1e5          # mGal per (kg/m3 . m)

REGION = (109.5, 111.5, -8.2, -6.4)             # Central Java model window
SPACING = 0.06                                   # deg (~6.6 km) model tesseroids
N_ITER = 12
MU = 6.0e-4                                       # smoothness weight (tuned)
WRF2_FACTOR = 90.0                                 # RF-constraint weight (x A^2)
B_MIN = 30.0                                       # floor (m) — avoid zero-height tesseroids
B_MAX = 12000.0                                   # cap basement depth (m)
DRHO_GRID = [-250., -300., -350., -400., -450., -500.]   # kg/m3 candidates
ZREF_GRID = [2500., 3000., 3500.]                        # m — reference level


def residual_gravity():
    boug = xr.open_dataarray(D / "bouguer_cjava.nc")
    lat, lon = boug.lat.values, boug.lon.values
    dlat = abs(lat[1] - lat[0])
    reg = gaussian_filter(boug.values, sigma=25.0 / (111.0 * dlat), mode="nearest")
    res = boug.values - reg
    return RGI((lat, lon), res, bounds_error=False, fill_value=0.0)


def smoothness_operator(ny, nx):
    """First-difference R over the 2-D grid (rows=lat, cols=lon), stacked."""
    n = ny * nx
    idx = np.arange(n).reshape(ny, nx)
    rows, cols, vals = [], [], []
    k = 0
    for a, b in np.c_[idx[:, :-1].ravel(), idx[:, 1:].ravel()]:      # x-neighbours
        rows += [k, k]; cols += [a, b]; vals += [1.0, -1.0]; k += 1
    for a, b in np.c_[idx[:-1, :].ravel(), idx[1:, :].ravel()]:      # y-neighbours
        rows += [k, k]; cols += [a, b]; vals += [1.0, -1.0]; k += 1
    return sparse.csr_matrix((vals, (rows, cols)), shape=(k, n))


def forward(lon2d, lat2d, b, drho, zref, obs):
    """Gravity (mGal) of the basement relief b(x,y) undulating around z_ref.

    Uieda-style: tesseroids between the reference level z_ref and the interface b,
    with density contrast drho where b>z_ref (extra sediment -> negative g) and
    -drho where b<z_ref (basement high -> positive g)."""
    surface = R_E - b                                       # interface radius
    reference = np.full(lon2d.shape, R_E - zref)            # reference-level radius
    dens = np.where(b >= zref, drho, -drho)                 # sign flip about z_ref
    layer = hm.tesseroid_layer((lon2d[0], lat2d[:, 0]), surface=surface,
                               reference=reference, properties={"density": dens})
    g = layer.tesseroid_layer.gravity(obs, field="g_z")
    return np.asarray(g)


def invert(lon2d, lat2d, dobs, drho, zref, mu=MU, n_iter=N_ITER,
           rf_idx=None, rf_z=None, wrf2=0.0):
    """Regularised Bott inversion (Uieda & Barbosa 2017, eq. 13) for basement b.

    When rf_idx/rf_z are given, a soft equality constraint b[cell]=RF-depth is
    added (weight wrf2) — the RF-CONSTRAINED joint inversion (seismology anchor).
    """
    ny, nx = lon2d.shape
    obs = (lon2d, lat2d, np.full(lon2d.shape, R_E))
    A = TWO_PI_G * drho                                     # mGal per m (scalar)
    Rm = smoothness_operator(ny, nx)
    RtR = (Rm.T @ Rm).tocsr()
    n = ny * nx
    LHS = (A * A) * sparse.identity(n, format="csr") + mu * RtR
    if rf_idx is not None and wrf2 > 0:
        sel = sparse.csr_matrix((np.full(len(rf_idx), wrf2), (rf_idx, rf_idx)), shape=(n, n))
        LHS = LHS + sel
    b = np.full(n, zref)                                    # start at the reference
    hist = []
    for it in range(n_iter):
        d = forward(lon2d, lat2d, b.reshape(ny, nx), drho, zref, obs).ravel()
        r = dobs.ravel() - d
        hist.append(float(np.sqrt(np.mean(r**2))))
        rhs = A * r - mu * (RtR @ (b - zref))
        if rf_idx is not None and wrf2 > 0:
            rhs[rf_idx] += wrf2 * (rf_z - b[rf_idx])
        db = spsolve(LHS, rhs)
        b = np.clip(b + db, B_MIN, B_MAX)
    d = forward(lon2d, lat2d, b.reshape(ny, nx), drho, zref, obs).ravel()
    hist.append(float(np.sqrt(np.mean((dobs.ravel() - d)**2))))
    return b.reshape(ny, nx), d.reshape(ny, nx), hist


def rf_points():
    s = pd.read_csv(D / "sediment_rf.csv")
    s = s[s.kind.isin(["EDL", "SAM"]) & (s.h_sed_km > 0)].copy()
    s = s[(s.lon > REGION[0]) & (s.lon < REGION[1]) &
          (s.lat > REGION[2]) & (s.lat < REGION[3])]
    return s


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    fres = residual_gravity()
    lon2d, lat2d = vd.grid_coordinates(REGION, spacing=SPACING)
    dobs = fres(np.stack([lat2d, lon2d], axis=-1))
    s = rf_points()
    print(f"Model grid {lon2d.shape}, RF calibration points: {len(s)}")

    # --- estimate (z_ref, drho) from RF known depths (Uieda sec. 2.6.2) --------
    cal = []
    for zref in ZREF_GRID:
        for drho in DRHO_GRID:
            b, dpred, hist = invert(lon2d, lat2d, dobs, drho, zref)
            fb = RGI((lat2d[:, 0], lon2d[0]), b, bounds_error=False, fill_value=np.nan)
            bpred = fb(np.c_[s.lat, s.lon]) / 1000.0        # km
            m = np.isfinite(bpred)
            mse = float(np.mean((s.h_sed_km.values[m] - bpred[m])**2))
            cal.append((zref, drho, mse, hist[-1]))
    cal = np.array(cal)
    k = int(np.argmin(cal[:, 2]))
    zref_best, drho_best = float(cal[k, 0]), float(cal[k, 1])
    print(f"-> RF-calibrated: z_ref={zref_best:.0f} m, drho={drho_best:.0f} kg/m3, "
          f"RF-MSE={cal[k,2]:.2f} km^2, data-RMS={cal[k,3]:.2f} mGal")
    # drho slice at best z_ref for the calibration plot
    cal_drho = cal[cal[:, 0] == zref_best][:, [1, 2]]

    # --- FINAL model: RF-CONSTRAINED joint inversion (seismology anchor) -------
    latc, lonc = lat2d[:, 0], lon2d[0]
    ny, nx = lon2d.shape
    col = np.array([int(np.argmin(np.abs(lonc - lo))) for lo in s.lon.values])
    row = np.array([int(np.argmin(np.abs(latc - la))) for la in s.lat.values])
    flat = row * nx + col
    zt = s.h_sed_km.values * 1000.0                          # RF depth (m)
    cells = {}
    for f_, z_ in zip(flat, zt):
        cells.setdefault(int(f_), []).append(z_)
    rf_idx = np.array(sorted(cells))
    rf_z = np.array([np.mean(cells[c]) for c in rf_idx])
    A = TWO_PI_G * drho_best
    wrf2 = WRF2_FACTOR * A * A
    b, dpred, hist = invert(lon2d, lat2d, dobs, drho_best, zref_best,
                            rf_idx=rf_idx, rf_z=rf_z, wrf2=wrf2)
    thick = b / 1000.0                                       # km
    da = xr.DataArray(thick, coords={"lat": latc, "lon": lonc}, dims=["lat", "lon"])
    da.to_netcdf(D / "sediment_uieda3d.nc")

    fb = RGI((latc, lonc), thick, bounds_error=False, fill_value=np.nan)
    s = s.copy(); s["h_grav"] = fb(np.c_[s.lat, s.lon])
    s = s.dropna(subset=["h_grav"])
    r, pv = pearsonr(s.h_grav, s.h_sed_km)
    rms = float(np.sqrt(np.mean((s.h_grav - s.h_sed_km)**2)))
    print(f"Inverted vs RF: r={r:+.2f} (p={pv:.2f})  RMS={rms:.2f} km  N={len(s)}")

    ext = [lonc.min(), lonc.max(), latc.min(), latc.max()]

    # ---- Figure 1: gravity fit -----------------------------------------------
    fig, ax = plt.subplots(1, 3, figsize=(15.5, 4.8))
    vlim = np.nanpercentile(np.abs(dobs), 98)
    for a, dat, t in [(ax[0], dobs, "(a) Observed residual gravity"),
                      (ax[1], dpred, "(b) Predicted (tesseroid model)"),
                      (ax[2], dobs - dpred, "(c) Data residual (fit)")]:
        im = a.imshow(dat, origin="lower", extent=ext, cmap="RdBu_r",
                      vmin=-vlim, vmax=vlim, aspect="auto")
        add_coast(a, REGION)
        a.set_title(t, fontweight="bold", fontsize=11, pad=8)
        a.set_xlabel("Longitude (°E)")
        fig.colorbar(im, ax=a, fraction=0.046, pad=0.03, label="mGal")
    ax[0].set_ylabel("Latitude (°)")
    fig.suptitle(f"Uieda-style tesseroid inversion — gravity fit "
                 f"(final RMS {hist[-1]:.1f} mGal)", fontsize=14, fontweight="bold", y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(FIG / "cj_uieda_fit.png", dpi=200); plt.close(fig)
    print("Wrote cj_uieda_fit.png")

    # ---- Figure 2: 3-D model, drho calibration, inverted-vs-RF ---------------
    fig = plt.figure(figsize=(16, 5.4))
    gs = GridSpec(1, 3, width_ratios=[1.25, 0.9, 0.95], wspace=0.5)
    vmax_t = np.nanpercentile(thick, 98)
    prof_j = int(np.argmax(np.nanmean(thick, axis=1)))
    prof_lat = float(latc[prof_j])
    a = fig.add_subplot(gs[0])
    im = a.imshow(thick, origin="lower", extent=ext, cmap="turbo", aspect="auto",
                  vmin=thick.min(), vmax=vmax_t)
    a.scatter(s.lon, s.lat, c=s.h_sed_km, cmap="turbo", s=46, edgecolor="k", lw=.6,
              vmin=thick.min(), vmax=vmax_t)
    a.plot([lonc.min(), lonc.max()], [prof_lat, prof_lat], color="k", lw=1.6, ls=(0, (6, 3)))
    a.text(lonc.min() + 0.03, prof_lat + 0.05, "A", fontweight="bold", fontsize=12)
    a.text(lonc.max() - 0.12, prof_lat + 0.05, "A'", fontweight="bold", fontsize=12)
    add_coast(a, REGION)
    a.set_title("(a) RF-constrained 3-D sediment thickness", fontweight="bold", fontsize=11, pad=8)
    a.set_xlabel("Longitude (°E)"); a.set_ylabel("Latitude (°)")
    fig.colorbar(im, ax=a, fraction=0.046, pad=0.03, label="sediment thickness (km)")
    a.text(0.02, 0.02, "dots = RF (same colour scale) · A–A' = section",
           transform=a.transAxes, fontsize=8.5, style="italic", color="white",
           bbox=dict(boxstyle="round", fc="#00000066", ec="none"))
    a = fig.add_subplot(gs[1])
    a.plot(cal_drho[:, 0], cal_drho[:, 1], "o-", color="#065A82")
    a.axvline(drho_best, color="#B0512F", ls="--")
    a.set_xlabel("density contrast Δρ (kg/m³)"); a.set_ylabel("MSE vs RF (km²)")
    a.set_title(f"(b) Δρ calibrated by RF (z_ref {zref_best/1000:.1f} km)",
                fontweight="bold", fontsize=11, pad=8)
    a.grid(alpha=.3)
    a = fig.add_subplot(gs[2])
    a.scatter(s.h_sed_km, s.h_grav, s=32, color="#1C7293", edgecolor="white", lw=.4)
    lim = max(s.h_sed_km.max(), s.h_grav.max()) * 1.05
    a.plot([0, lim], [0, lim], "k--", lw=1)
    a.set_xlabel("RF sediment thickness (km)"); a.set_ylabel("Gravity 3-D thickness (km)")
    a.set_title("(c) RF-constrained gravity vs RF", fontweight="bold", fontsize=11, pad=8)
    a.text(0.05, 0.95, f"r = {r:+.2f}\nRMS = {rms:.1f} km\nn = {len(s)}",
           transform=a.transAxes, va="top", fontsize=11,
           bbox=dict(boxstyle="round", fc="#FFF3E0", ec="#C98A1A"))
    a.grid(alpha=.3); a.set_xlim(0, lim); a.set_ylim(0, lim)
    fig.suptitle("Central Java — RF-constrained 3-D gravity basin model (Uieda & Barbosa 2017)",
                 fontsize=14, fontweight="bold", y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(FIG / "cj_uieda_vs_rf.png", dpi=200); plt.close(fig)
    print("Wrote cj_uieda_vs_rf.png")

    # ---- Figure 3: representative DENSITY cross-section -----------------------
    density_section(lonc, latc, thick, s, drho_best, lat0=prof_lat)


def density_section(lonc, latc, thick, s, drho, rho_base=2670.0, lat0=None):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # profile at the latitude of the thickest mean sediment (through the depocentre)
    j = int(np.argmax(np.nanmean(thick, axis=1))) if lat0 is None else int(np.argmin(np.abs(latc - lat0)))
    lat0 = latc[j]
    b_prof = thick[j]                                  # km, basement depth along profile
    x_km = (lonc - lonc.mean()) * 111.32 * np.cos(np.deg2rad(lat0))
    zmax = float(np.nanmax(b_prof)) * 1.5 + 1.0
    dz = 0.05
    depth = np.arange(0, zmax + dz, dz)
    rho_sed = rho_base + drho                          # kg/m3
    D = np.where(depth[:, None] < b_prof[None, :], rho_sed, rho_base)

    fig, a = plt.subplots(figsize=(13, 3.8))
    pm = a.pcolormesh(x_km, depth, D, cmap="YlOrBr", shading="auto",
                      vmin=rho_sed - 40, vmax=rho_base + 40)
    a.plot(x_km, b_prof, color="#10233A", lw=2.2, label="basement (gravity inversion)")
    near = s[np.abs(s.lat - lat0) < 0.25]
    xr = (near.lon.values - lonc.mean()) * 111.32 * np.cos(np.deg2rad(lat0))
    a.scatter(xr, near.h_sed_km, c="#0353A4", s=48, zorder=6, edgecolor="white",
              label="RF basement (±0.25°)")
    a.invert_yaxis()
    a.set_xlabel("Distance W–E (km)"); a.set_ylabel("Depth (km)")
    a.set_xlim(x_km.min(), x_km.max()); a.set_ylim(zmax, 0)
    # vertical exaggeration from the rendered axes geometry
    fig.canvas.draw()
    bb = a.get_position(); fw, fh = fig.get_size_inches()
    ve = ((x_km.max() - x_km.min()) / (bb.width * fw)) / (zmax / (bb.height * fh))
    a.set_title(f"Representative density cross-section at {lat0:.2f}°S  "
                f"(vertical exaggeration ×{ve:.0f})", fontweight="bold", fontsize=12)
    a.legend(loc="lower right", fontsize=9, framealpha=.9)
    cb = fig.colorbar(pm, ax=a, fraction=0.03, pad=0.015)
    cb.set_label("density (kg/m³)", fontsize=9)
    a.text(0.012, 0.90, f"sediment  ρ≈{rho_sed:.0f} kg/m³  (Δρ={drho:.0f})",
           transform=a.transAxes, fontsize=9.5, color="#5A3A00", va="top", fontweight="bold")
    a.text(0.012, 0.16, f"basement  ρ≈{rho_base:.0f} kg/m³", transform=a.transAxes,
           fontsize=9.5, color="white", va="top", fontweight="bold")
    fig.tight_layout(); fig.savefig(FIG / "cj_uieda_density_section.png", dpi=200)
    plt.close(fig)
    print("Wrote cj_uieda_density_section.png")


if __name__ == "__main__":
    main()
