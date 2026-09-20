"""
Central Java — validation of satellite gravity against the RF/Vs shear-velocity
model, and a demonstration of seismology as a constraint for gravity interpretation.

Question (supervisor): does the satellite Bouguer field, on its own, recover the
sediment/velocity structure that receiver functions and the Vs model reveal?

Findings (printed + plotted):
  * DIRECT correlation of residual Bouguer gravity with RF sediment thickness is
    weak and not significant (r ~ 0.1) at every regional-cut wavelength — the
    shallow basin signal (tens of mGal) is buried under Moho/arc mass (hundreds).
  * That is the non-uniqueness wall, quantified: gravity ALONE cannot be inverted
    for sediment here without an external depth/velocity anchor.
  * Receiver functions + the Vs model supply that anchor (absolute depth &
    density), turning the ambiguous field into the RF-constrained sediment model.

Outputs (figures/rf_java/):
  cj_gravity_vs_validation.png     map + scatter + signal-budget
  cj_seismology_constraint.png     RF-constrained model + Vs anchor + message

Run (fbt):  python rf_gravity_java/validate_gravity_vs.py
"""
from __future__ import annotations
import sys, pathlib
import numpy as np, pandas as pd, xarray as xr
from scipy.ndimage import gaussian_filter
from scipy.interpolate import RegularGridInterpolator as RGI
from scipy.stats import pearsonr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C

D = C.DATA_PROCESSED
FIG = C.FIGURES
XLSX = pathlib.Path("/Users/maswiet/Downloads/digitized_velocity_models_all_stations.xlsx")
G = 41.93  # mGal per (g/cm3 . km) infinite-slab constant


def residual(boug, lat, cut_km=25.0):
    dlat = abs(lat[1] - lat[0])
    reg = gaussian_filter(boug, sigma=cut_km / (111.0 * dlat), mode="nearest")
    return boug - reg


def load():
    boug = xr.open_dataarray(D / "bouguer_cjava.nc")
    lat, lon = boug.lat.values, boug.lon.values
    res = residual(boug.values, lat)
    s = pd.read_csv(D / "sediment_rf.csv")
    s = s[s.kind.isin(["EDL", "SAM"]) & (s.h_sed_km > 0)].copy()
    fB = RGI((lat, lon), boug.values, bounds_error=False, fill_value=np.nan)
    fR = RGI((lat, lon), res, bounds_error=False, fill_value=np.nan)
    s["boug"] = fB(np.c_[s.lat, s.lon]); s["res"] = fR(np.c_[s.lat, s.lon])
    s = s.dropna(subset=["res", "boug"])
    return boug, lat, lon, res, s


def stats(s):
    print(f"N stations (resolved, in grid): {len(s)}")
    print("Regional-cut wavelength sweep (residual vs RF sediment thickness):")
    out = []
    boug = xr.open_dataarray(D / "bouguer_cjava.nc"); lat = boug.lat.values
    fcoords = np.c_[s.lat, s.lon]
    for cut in [15, 20, 25, 30, 40, 60]:
        r = residual(boug.values, lat, cut)
        v = RGI((lat, boug.lon.values), r, bounds_error=False, fill_value=np.nan)(fcoords)
        m = np.isfinite(v); rr, pv = pearsonr(v[m], s.h_sed_km.values[m])
        out.append((cut, rr, pv)); print(f"   cut {cut:3d} km : r={rr:+.3f}  p={pv:.2f}")
    rr, pv = pearsonr(s.res, s.h_sed_km)
    return rr, pv


def signal_budget(boug, s):
    """Rough variance budget: observed Bouguer vs the sediment slab it could carry."""
    boug_std = float(np.nanstd(boug.values))
    dbg = float(np.nanmax(boug.values) - np.nanmin(boug.values))
    sed_drho = 0.30   # g/cm3 typical shallow sediment-basement contrast
    sed_dg_std = G * sed_drho * float(np.nanstd(s.h_sed_km))
    sed_dg_max = G * sed_drho * float(s.h_sed_km.max())
    print(f"\nSignal budget:  Bouguer span ~{dbg:.0f} mGal (std {boug_std:.0f})")
    print(f"   sediment slab (Δρ={sed_drho}) can only carry std ~{sed_dg_std:.0f}, "
          f"max ~{sed_dg_max:.0f} mGal  -> ~{100*sed_dg_std/boug_std:.0f}% of the field")
    return boug_std, sed_dg_std, sed_dg_max, dbg


# --------------------------------------------------------------------------
def fig_validation(boug, lat, lon, res, s, r, pv, budget):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    fig = plt.figure(figsize=(15.5, 5.6))
    gs = GridSpec(1, 3, width_ratios=[1.2, 1.0, 0.85], wspace=0.5)

    # (a) map: residual gravity + RF stations coloured by sediment thickness
    ax = fig.add_subplot(gs[0])
    ext = [lon.min(), lon.max(), lat.min(), lat.max()]
    im = ax.imshow(res, origin="lower", extent=ext, cmap="RdBu_r",
                   vmin=-40, vmax=40, aspect="auto")
    sc = ax.scatter(s.lon, s.lat, c=s.h_sed_km, cmap="viridis", s=40,
                    edgecolor="k", lw=.5, vmax=np.percentile(s.h_sed_km, 95))
    ax.set_title("(a) Residual gravity vs RF sediment sites", fontweight="bold", fontsize=12)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03); cb.set_label("residual (mGal)", fontsize=9)
    cb2 = fig.colorbar(sc, ax=ax, orientation="horizontal", fraction=0.05, pad=0.16)
    cb2.set_label("RF sediment thickness (km)", fontsize=9)

    # (b) scatter residual vs sediment thickness
    ax = fig.add_subplot(gs[1])
    ax.scatter(s.h_sed_km, s.res, s=32, color="#065A82", edgecolor="white", lw=.4, alpha=.85)
    b, a = np.polyfit(s.h_sed_km, s.res, 1)
    xx = np.linspace(0, s.h_sed_km.max(), 20)
    ax.plot(xx, b * xx + a, "r--", lw=2)
    ax.set_xlabel("RF sediment thickness (km)"); ax.set_ylabel("Residual Bouguer (mGal)")
    ax.set_title("(b) Gravity ALONE: no significant relation", fontweight="bold", fontsize=12)
    ax.text(0.04, 0.94, f"Pearson r = {r:+.2f}\np = {pv:.2f}  (n={len(s)})\nslope = {b:+.1f} mGal/km",
            transform=ax.transAxes, va="top", fontsize=11,
            bbox=dict(boxstyle="round", fc="#FFF3E0", ec="#C98A1A"))
    ax.grid(alpha=.3)

    # (c) signal budget bar
    ax = fig.add_subplot(gs[2])
    boug_std, sed_dg_std, sed_dg_max, dbg = budget
    bars = ["Observed\nBouguer\n(std)", "Sediment\ncan carry\n(std)"]
    vals = [boug_std, sed_dg_std]
    ax.bar(bars, vals, color=["#1C7293", "#C98A1A"], edgecolor="k")
    for i, v in enumerate(vals):
        ax.text(i, v + 2, f"{v:.0f}", ha="center", fontweight="bold")
    ax.set_ylabel("mGal (std of field)")
    ax.set_title("(c) Why: sediment is a\nsmall part of the field", fontweight="bold", fontsize=12)
    ax.text(0.5, 0.80, f"sediment ≈ {100*sed_dg_std/boug_std:.0f}% of\nthe Bouguer variance",
            transform=ax.transAxes, ha="center", fontsize=10.5, color="#B0512F", fontweight="bold")
    fig.suptitle("Central Java — satellite gravity cannot resolve the sediment on its own",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG / "cj_gravity_vs_validation.png", dpi=200)
    print("Wrote cj_gravity_vs_validation.png")


def fig_constraint(s):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec
    sed = xr.open_dataarray(D / "sediment_thickness_grav.nc")
    lat, lon = sed.lat.values, sed.lon.values
    fig = plt.figure(figsize=(14.5, 5.6))
    gs = GridSpec(1, 3, width_ratios=[1.15, 0.85, 0.95], wspace=0.6)

    ax = fig.add_subplot(gs[0])
    im = ax.imshow(sed.values, origin="lower",
                   extent=[lon.min(), lon.max(), lat.min(), lat.max()],
                   cmap="turbo", aspect="auto")
    ax.scatter(s.lon, s.lat, c="k", s=8)
    ax.set_title("(a) RF-CONSTRAINED sediment model", fontweight="bold", fontsize=12)
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03); cb.set_label("sediment thickness (km)", fontsize=9)

    # (b) flagship Vs profile as the depth anchor
    ax = fig.add_subplot(gs[1])
    try:
        v = pd.read_csv(D / "vs_profiles.csv")
        vb = v[v.code == "BI4"].sort_values("depth_km")
        ax.step(vb.vs, vb.depth_km, where="post", color="#02C39A", lw=2.5)
    except Exception:
        pass
    ax.invert_yaxis(); ax.set_xlim(0, 5)
    ax.set_xlabel("Vs (km/s)"); ax.set_ylabel("Depth (km)")
    ax.set_title("(b) The anchor: absolute Vs(z)\n(RF inversion, stn BI4)",
                 fontweight="bold", fontsize=11)
    ax.grid(alpha=.3)

    # (c) message
    ax = fig.add_subplot(gs[2]); ax.axis("off")
    ax.text(0.0, 1.0,
            "Seismology as constraint\n\n"
            "1.  Gravity alone: density×depth\n     is non-unique (panel b prev).\n\n"
            "2.  RF gives ABSOLUTE depth &\n     Vs at each station.\n\n"
            "3.  Feed RF depths in → fix the\n     density scale → a coherent\n     basin model gravity could\n     not produce alone.\n\n"
            "→ gravity + seismology is far\n   more powerful than either.",
            va="top", ha="left", fontsize=11.5, color="#10233A")
    fig.suptitle("Central Java — receiver functions unlock the gravity interpretation",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(FIG / "cj_seismology_constraint.png", dpi=200)
    print("Wrote cj_seismology_constraint.png")


def main():
    boug, lat, lon, res, s = load()
    r, pv = stats(s)
    budget = signal_budget(boug, s)
    fig_validation(boug, lat, lon, res, s, r, pv, budget)
    fig_constraint(s)


if __name__ == "__main__":
    main()
