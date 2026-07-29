"""
plot_pygmt — publication-quality Moho map with PyGMT (high-resolution coastlines).

Renders the estimated Moho grid with GMT/GSHHG shorelines (much finer than the
matplotlib/cartopy previews — important for the Indonesian archipelago), Moho
contours, the seismic Moho points, and tectonic context lines.

Run (in the fbt env):
    python moho_indonesia/plot_pygmt.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import pygmt
import xarray as xr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402

# Approximate tectonic context lines (lon, lat) — orientation only.
SUNDA_BANDA_TRENCH = np.array([
    (92.5, 6.0), (93.5, 3.5), (95.0, 1.0), (97.0, -1.5), (99.0, -3.5),
    (101.0, -5.2), (103.5, -6.6), (106.5, -8.0), (110.0, -9.2), (113.0, -10.2),
    (116.0, -10.8), (119.0, -10.9), (121.5, -10.4), (123.5, -9.2), (125.0, -7.8),
    (126.5, -6.8), (128.0, -6.5),
])
SUMATRAN_FAULT = np.array([
    (95.5, 5.3), (97.0, 4.0), (98.5, 2.4), (99.6, 0.9), (100.6, -0.6),
    (101.6, -2.1), (102.6, -3.6), (103.6, -5.0), (104.3, -5.9),
])


def plot(grid_path=C.GRID_MOHO, out=C.FIGURES / "real_moho_pygmt.png",
         resolution="h", cmap_series=(0, 50, 5), title="Moho depth of Indonesia"):
    grid = xr.open_dataarray(grid_path)
    if "longitude" in grid.dims:
        grid = grid.rename({"longitude": "lon", "latitude": "lat"})
    region = list(C.REGION)
    proj = "M20c"

    # Resample to a fine mesh, then apply a Gaussian filter so both the image and
    # the contour lines are smooth and flowing (the raw 0.5 deg grid gives angular
    # contours). grdfilter uses spherical distances; "g150k" ~ 25 km sigma.
    fine_lon = np.arange(region[0], region[1] + 1e-9, 0.1)
    fine_lat = np.arange(region[2], region[3] + 1e-9, 0.1)
    from scipy.ndimage import gaussian_filter
    grid = grid.interp(lon=fine_lon, lat=fine_lat, method="cubic")
    grid = grid.copy(data=gaussian_filter(grid.values, sigma=2.5, mode="nearest"))

    seismic = mu.load_seismic_moho()

    fig = pygmt.Figure()
    pygmt.config(FONT_TITLE="16p,Helvetica-Bold", FONT_ANNOT_PRIMARY="9p",
                 MAP_FRAME_TYPE="plain",            # thin simple border (no railroad)
                 MAP_FRAME_PEN="0.8p,gray25",
                 MAP_TICK_LENGTH_PRIMARY="0.12c",
                 MAP_TICK_PEN_PRIMARY="0.6p,gray25")
    pygmt.makecpt(cmap="viridis", series=list(cmap_series))

    # Moho grid image.
    fig.grdimage(grid=grid, region=region, projection=proj, cmap=True,
                 frame=["af", f'WSne+t{title}'])
    # Smooth thin contours every 5 km, annotated every 10 km; bold 35 km line.
    fig.grdcontour(grid=grid, levels=5, annotation=10,
                   pen="0.3p,gray25", region=region, projection=proj)
    fig.grdcontour(grid=grid, levels=[35], pen="1.4p,white",
                   region=region, projection=proj)
    # High-resolution coastlines (GSHHG).
    fig.coast(region=region, projection=proj, resolution=resolution,
              shorelines="1/0.5p,gray10", borders="1/0.3p,gray40")
    # Tectonic context.
    fig.plot(x=SUNDA_BANDA_TRENCH[:, 0], y=SUNDA_BANDA_TRENCH[:, 1],
             pen="2p,black", label="Sunda-Banda trench (approx.)")
    fig.plot(x=SUMATRAN_FAULT[:, 0], y=SUMATRAN_FAULT[:, 1],
             pen="1.5p,red3", label="Sumatran Fault (approx.)")
    # Seismic Moho points (filled by the same CPT). A dummy off-region point
    # provides the legend entry (auto-legend is skipped for variable colors).
    fig.plot(x=[region[0] - 10], y=[region[2] - 10], style="c0.20c",
             fill="gray70", pen="0.5p,black", label="Seismic Moho station")
    fig.plot(x=seismic.longitude, y=seismic.latitude, fill=seismic.depth_km,
             cmap=True, style="c0.20c", pen="0.5p,black")
    fig.legend(position="jBL+o0.2c", box="+gwhite@15+p0.5p,gray50")
    # Slim, short colorbar (annotate every 10 km, tick every 5) — not full-height.
    fig.colorbar(frame="xa10f5+lMoho depth (km)",
                 position="JMR+o0.5c/0c+w5.5c/0.28c")

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=250)
    print("Wrote", out)


if __name__ == "__main__":
    plot()
