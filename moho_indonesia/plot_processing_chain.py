"""
plot_processing_chain — U&B (2017) Fig. 8 style: the gravity data-reduction chain.

Six map panels: (a) gravity disturbance, (b) topography/bathymetry, (c) topographic
effect, (d) Bouguer disturbance, (e) CRUST1.0 sediment effect, (f) sediment-free
Bouguer disturbance (the inversion input). Uses the GGM (GOCO06S) gravity path.

Run (fbt env):  python moho_indonesia/plot_processing_chain.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import cartopy.crs as ccrs               # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402
import run_real             # noqa: E402
from calibrate import sediment_effect    # noqa: E402

REGION = [94, 141, -11, 6.5]
# Natural map proportions (latitude span / longitude span) so panels are undistorted.
BOX_RATIO = (REGION[3] - REGION[2]) / (REGION[1] - REGION[0])


def _panel(fig, pos, lon, lat, field, title, cmap, unit, vlim=None):
    ax = fig.add_subplot(pos, projection=ccrs.PlateCarree())
    ax.set_extent(REGION, crs=ccrs.PlateCarree())
    ax.set_aspect("auto")            # fill a box whose shape is set naturally below
    ax.set_box_aspect(BOX_RATIO)
    if vlim is None:
        v = float(np.nanpercentile(np.abs(field), 98))
        vmin, vmax = -v, v
    else:
        vmin, vmax = vlim
    pcm = ax.pcolormesh(lon, lat, field, cmap=cmap, vmin=vmin, vmax=vmax,
                        shading="auto", transform=ccrs.PlateCarree())
    try:
        ax.coastlines("50m", linewidth=0.4, color="0.25")
    except Exception:
        pass
    gl = ax.gridlines(draw_labels=True, linewidth=0.2, color="0.85")
    gl.top_labels = gl.right_labels = False
    gl.xlabel_style = gl.ylabel_style = {"size": 7}
    ax.set_title(title, fontsize=11)
    cb = fig.colorbar(pcm, ax=ax, orientation="horizontal", pad=0.09,
                      shrink=0.92, extend="both")
    cb.set_label(unit, fontsize=8)
    cb.ax.tick_params(labelsize=7)


def main():
    lon, lat = run_real.build_grid(0.5)
    print("Fetching GGM disturbance + topography ...")
    topo, disturbance = run_real.fetch_data(lon, lat, "30m", "ggm")
    tess, dens = mu.topography_to_tesseroids(topo, lon, lat)
    topo_eff = mu.tesseroid_gravity_grid(tess, dens, lon, lat, height_m=run_real.HEIGHT)
    bouguer = disturbance - topo_eff
    print("Computing CRUST1.0 sediment effect ...")
    sed_eff = sediment_effect(lon, lat)
    sed_free = bouguer - sed_eff

    fig = plt.figure(figsize=(15, 6.6))
    gs = fig.add_gridspec(2, 3, hspace=0.28, wspace=0.14,
                          left=0.04, right=0.98, bottom=0.04, top=0.95)
    _panel(fig, gs[0, 0], lon, lat, disturbance, "(a) Gravity disturbance", "RdBu_r", "mGal")
    _panel(fig, gs[0, 1], lon, lat, topo, "(b) Topography / bathymetry", "gist_earth", "m", vlim=(-6000, 3000))
    _panel(fig, gs[0, 2], lon, lat, topo_eff, "(c) Topographic effect", "RdBu_r", "mGal")
    _panel(fig, gs[1, 0], lon, lat, bouguer, "(d) Bouguer disturbance", "RdBu_r", "mGal")
    _panel(fig, gs[1, 1], lon, lat, sed_eff, "(e) Sediment effect (CRUST1.0)", "Blues_r", "mGal", vlim=(-200, 0))
    _panel(fig, gs[1, 2], lon, lat, sed_free, "(f) Sediment-free Bouguer (inversion input)", "RdBu_r", "mGal")

    out = C.FIGURES / "processing_chain.png"
    fig.savefig(out, dpi=160)
    print("Wrote", out)


if __name__ == "__main__":
    main()
