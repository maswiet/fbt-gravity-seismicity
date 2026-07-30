"""
plot_validation — polished Moho-residual validation figure (U&B Fig. 12b style).

Two equal-size panels: (a) residual (estimated − seismic) at the seismic stations
on a high-resolution coastline map with a short horizontal colourbar, and
(b) the residual histogram. Reads the current GRID_MOHO.

Run (fbt env):  python moho_indonesia/plot_validation.py
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
import cartopy.crs as ccrs               # noqa: E402
import cartopy.feature as cfeature       # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402

VMAX = 8.0


def main(out=C.FIGURES / "validation_seismic.png"):
    d = xr.open_dataarray(C.GRID_MOHO)
    interp = RegularGridInterpolator((d.latitude.values, d.longitude.values),
                                     d.values, bounds_error=False, fill_value=np.nan)
    seis = mu.load_seismic_moho()
    est = interp(np.column_stack([seis.latitude, seis.longitude]))
    ok = np.isfinite(est)
    lon, lat = seis.longitude.values[ok], seis.latitude.values[ok]
    diff = est[ok] - seis.depth_km.values[ok]

    plt.rcParams.update({"font.size": 11, "axes.titlesize": 12})
    region = [94, 141, -11, 6.5]         # trim to Indonesia for the residual map
    # Natural map proportions: box height/width = latitude span / longitude span.
    box_ratio = (region[3] - region[2]) / (region[1] - region[0])
    fig = plt.figure(figsize=(15, 4.6))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1], wspace=0.18,
                          left=0.05, right=0.97, bottom=0.10, top=0.92)

    # ---- (a) residual map ----
    ax = fig.add_subplot(gs[0], projection=ccrs.PlateCarree())
    ax.set_extent(region, crs=ccrs.PlateCarree())
    # 'auto' fills the box; a natural box_aspect makes that box the right shape,
    # so the map looks undistorted instead of vertically stretched.
    ax.set_aspect("auto")
    ax.set_box_aspect(box_ratio)
    try:
        ax.add_feature(cfeature.LAND.with_scale("10m"), facecolor="#f4f1ea", zorder=0)
        ax.add_feature(cfeature.OCEAN.with_scale("10m"), facecolor="#e8f0f5", zorder=0)
        ax.coastlines("10m", linewidth=0.5, color="0.35")
    except Exception:
        ax.coastlines("50m", linewidth=0.5, color="0.35")
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, color="0.85")
    gl.top_labels = gl.right_labels = False
    sc = ax.scatter(lon, lat, c=diff, cmap="RdBu_r", vmin=-VMAX, vmax=VMAX,
                    s=55, edgecolor="k", linewidth=0.5, zorder=5,
                    transform=ccrs.PlateCarree())
    ax.set_title("(a) Moho residual at seismic stations", pad=8)
    # short horizontal colourbar under the map
    cax = ax.inset_axes([0.15, -0.16, 0.70, 0.045])
    cb = fig.colorbar(sc, cax=cax, orientation="horizontal", extend="both")
    cb.set_label("estimated − seismic (km)", fontsize=10)
    cb.ax.tick_params(labelsize=9)

    # ---- (b) histogram (same box shape/size as the map) ----
    ax2 = fig.add_subplot(gs[1])
    ax2.set_box_aspect(box_ratio)
    ax2.hist(diff, bins=np.arange(-15, 15.1, 1.5), color="#6b83c4",
             edgecolor="white", linewidth=0.7)
    ax2.axvline(diff.mean(), color="crimson", ls="--", lw=1.6,
                label=f"mean {diff.mean():+.1f} km")
    ax2.axvspan(diff.mean() - diff.std(), diff.mean() + diff.std(),
                color="crimson", alpha=0.07, label=f"±1σ = {diff.std():.1f} km")
    ax2.set_xlabel("estimated − seismic (km)")
    ax2.set_ylabel("count")
    ax2.set_title(f"(b) residual distribution (N = {ok.sum()})", pad=8)
    ax2.legend(frameon=False, fontsize=10)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.margins(x=0.02)

    fig.savefig(out, dpi=180)
    print(f"Wrote {out} | mean {diff.mean():+.2f}, std {diff.std():.2f} km, N={ok.sum()}")


if __name__ == "__main__":
    main()
