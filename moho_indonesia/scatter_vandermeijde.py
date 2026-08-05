"""van der Meijde (2013, Fig. 4 inset) style depth-depth scatter panels:
open circles against the 1:1 line, with +/-6 km (black) and +/-12 km (red)
deviation bands. Panels: this study, CRUST1.0 and GEMMA vs the 105 seismic
points, plus GEMMA vs CRUST1.0 over the model grid.

Run (fbt env):  python moho_indonesia/scatter_vandermeijde.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402


def crust1_interp():
    bnds = np.loadtxt(C.CRUST1_DIR / "crust1.bnds").reshape(180, 360, -1)
    moho = -bnds[:, :, 8]
    clat = np.arange(89.5, -90.0, -1.0)
    clon = np.arange(-179.5, 180.0, 1.0)
    return RegularGridInterpolator((clat[::-1], clon), moho[::-1, :],
                                   bounds_error=False, fill_value=np.nan)


def gemma_interp():
    g = xr.open_dataarray(C.DATA_EXTERNAL / "gemma" / "gemma_moho.nc")
    return RegularGridInterpolator((g.latitude.values, g.longitude.values), g.values,
                                   bounds_error=False, fill_value=np.nan)


def panel(ax, x, y, xlabel, ylabel, title, lim, band_units="km"):
    """van der Meijde-style panel: open circles, 1:1 line, +/-6 (black) / +/-12 (red)."""
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    lo, hi = lim
    xs = np.array([lo, hi])
    ax.plot(xs, xs, "-", color="0.15", lw=1.2, zorder=2)                 # 1:1
    for d, col in [(6, "k"), (12, "r")]:
        ax.plot(xs, xs + d, "--", color=col, lw=0.9, zorder=2)
        ax.plot(xs, xs - d, "--", color=col, lw=0.9, zorder=2)
    ax.scatter(x, y, s=26, facecolors="none", edgecolors="#1f1f1f", lw=0.7, zorder=3)
    diff = y - x
    rms = np.sqrt(np.mean(diff ** 2))
    p6 = 100 * np.mean(np.abs(diff) <= 6)
    p12 = 100 * np.mean(np.abs(diff) <= 12)
    slope = np.polyfit(x, y, 1)[0]
    txt = (f"N = {x.size}\nbias {diff.mean():+.1f} {band_units}\nRMS {rms:.1f} {band_units}\n"
           f"|dev|$\\leq$6: {p6:.0f}%\n|dev|$\\leq$12: {p12:.0f}%\nslope {slope:.2f}")
    ax.text(0.04, 0.96, txt, transform=ax.transAxes, va="top", ha="left", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="0.7", alpha=0.9))
    ax.set(xlim=lim, ylim=lim, xlabel=xlabel, ylabel=ylabel, title=title)
    ax.set_aspect("equal"); ax.set_xticks(np.arange(lo, hi + 1, 10))
    ax.set_yticks(np.arange(lo, hi + 1, 10))


def main():
    seis = mu.load_seismic_moho()
    slon, slat, sd = seis.longitude.values, seis.latitude.values, seis.depth_km.values

    d = xr.open_dataarray(C.GRID_MOHO)
    ours_i = RegularGridInterpolator((d.latitude.values, d.longitude.values), d.values,
                                     bounds_error=False, fill_value=np.nan)
    ci, gi = crust1_interp(), gemma_interp()
    pts = np.column_stack([slat, slon])
    ours, crust, gem = ours_i(pts), ci(pts), gi(pts)

    # model-vs-model over the Indonesia model grid (subsample for clarity)
    LON, LAT = np.meshgrid(d.longitude.values, d.latitude.values)
    sub = slice(None, None, 5)
    m = np.column_stack([LAT.ravel()[sub], LON.ravel()[sub]])
    ours_g = d.values.ravel()[sub]
    cg, gg = ci(m), gi(m)

    fig, axs = plt.subplots(2, 3, figsize=(16.5, 11))
    lim = (0, 70)          # vs seismic
    limg = (0, 60)         # model vs model
    panel(axs[0, 0], sd, ours, "seismic Moho (km)", "this study (km)",
          "(a) This study vs seismic", lim)
    panel(axs[0, 1], sd, crust, "seismic Moho (km)", "CRUST1.0 (km)",
          "(b) CRUST1.0 vs seismic", lim)
    panel(axs[0, 2], sd, gem, "seismic Moho (km)", "GEMMA (km)",
          "(c) GEMMA vs seismic", lim)
    panel(axs[1, 0], cg, ours_g, "CRUST1.0 (km)", "this study (km)",
          "(d) This study vs CRUST1.0 (grid)", limg)
    panel(axs[1, 1], gg, ours_g, "GEMMA (km)", "this study (km)",
          "(e) This study vs GEMMA (grid)", limg)
    panel(axs[1, 2], cg, gg, "CRUST1.0 (km)", "GEMMA (km)",
          "(f) GEMMA vs CRUST1.0 (grid)", limg)
    fig.suptitle("Moho depth: model vs seismic (top) and model vs model (bottom) "
                 "--- 1:1 line; dashed $\\pm$6 km black, $\\pm$12 km red", y=0.995,
                 fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.98))
    out = C.FIGURES / "scatter_vandermeijde.png"
    fig.savefig(out, dpi=170, bbox_inches="tight")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
