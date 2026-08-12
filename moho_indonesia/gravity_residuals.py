"""gravity_residuals — the elementary evidence a gravity-inversion paper must show
(reviewer): observed Bouguer disturbance, the gravity predicted by the recovered
Moho, and their residual. With mu ~ 0 the fit is near-perfect, which is itself the
point: the observed field is reproduced almost exactly, so any lack of Moho skill
comes from mapping non-Moho mass (sediment, slab, lateral density) into the interface.

Run (fbt env):  python moho_indonesia/gravity_residuals.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import xarray as xr

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import cartopy.crs as ccrs               # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402
import run_real             # noqa: E402


def main():
    lon2d, lat2d = run_real.build_grid(0.5)
    topo, disturbance = run_real.fetch_data(lon2d, lat2d, "30m", "ggm")
    tess, dens = mu.topography_to_tesseroids(topo, lon2d, lat2d)
    obs = disturbance - mu.tesseroid_gravity_grid(tess, dens, lon2d, lat2d,
                                                  height_m=run_real.HEIGHT)   # observed Bouguer

    moho = xr.open_dataarray(C.GRID_MOHO)          # featured recovered Moho (km)
    z_ref, drho = 35.0, 400.0
    forward = mu.make_tesseroid_forward(lon2d, lat2d, height_m=run_real.HEIGHT)
    pred = np.asarray(forward(moho.values.ravel() * 1000.0, z_ref, drho),
                      float).reshape(lon2d.shape)  # gravity of the recovered Moho
    resid = obs - pred
    rms = float(np.sqrt(np.nanmean(resid ** 2)))
    print(f"observed Bouguer: {np.nanmin(obs):.0f}..{np.nanmax(obs):.0f} mGal")
    print(f"gravity residual (observed - predicted): RMS {rms:.2f} mGal, "
          f"range {np.nanmin(resid):.0f}..{np.nanmax(resid):.0f} mGal")

    region = [94, 141, -15, 6.5]
    br = (region[3] - region[2]) / (region[1] - region[0])
    fig = plt.figure(figsize=(17, 4.6))
    gs = fig.add_gridspec(1, 3, wspace=0.42)
    panels = [("(a) Observed Bouguer disturbance", obs, "viridis", None),
              ("(b) Gravity of recovered Moho", pred, "viridis", None),
              (f"(c) Residual (RMS {rms:.1f} mGal)", resid, "RdBu_r", 30)]
    vmin, vmax = np.nanpercentile(obs, [2, 98])
    for k, (title, field, cmap, sym) in enumerate(panels):
        ax = fig.add_subplot(gs[k], projection=ccrs.PlateCarree())
        ax.set_extent(region); ax.set_aspect("auto"); ax.set_box_aspect(br)
        kw = dict(vmin=-sym, vmax=sym) if sym else dict(vmin=vmin, vmax=vmax)
        pcm = ax.pcolormesh(lon2d[0, :], lat2d[:, 0], field, cmap=cmap, shading="auto",
                            transform=ccrs.PlateCarree(), **kw)
        try:
            ax.coastlines("50m", lw=0.4, color="0.3")
        except Exception:
            pass
        gl = ax.gridlines(draw_labels=True, lw=0.2); gl.top_labels = gl.right_labels = False
        # slim colorbar as an inset anchored to the (box-aspected) map: half its height
        cax = ax.inset_axes([1.025, 0.27, 0.014, 0.46])
        cb = fig.colorbar(pcm, cax=cax)
        cb.set_label("mGal", fontsize=8.5); cb.ax.tick_params(labelsize=7.5, length=2)
        cb.outline.set_linewidth(0.3)
        ax.set_title(title)
    out = C.FIGURES / "gravity_residuals.png"
    fig.savefig(out, dpi=160, bbox_inches="tight")
    print("Wrote", out)


if __name__ == "__main__":
    main()
