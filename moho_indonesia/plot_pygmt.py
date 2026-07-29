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


def plot(grid_path=C.GRID_MOHO, out=C.FIGURES / "real_moho_pygmt.png",
         resolution="h", cmap_series=(0, 50, 5), title="Moho depth of Indonesia",
         region=None, tectonics=True, volcanoes=True):
    grid = xr.open_dataarray(grid_path)
    if "longitude" in grid.dims:
        grid = grid.rename({"longitude": "lon", "latitude": "lat"})
    region = list(region) if region is not None else list(C.REGION)
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
    # Real Indonesian tectonics (Pak Wiwit dataset in data/external/tectonics),
    # plotted if requested and present. GMT clips features to the region.
    tdir = C.DATA_EXTERNAL / "tectonics"
    if tectonics:
        features = [
            ("trench_edit.gmt", "1.8p,black", "Trench"),
            ("sesar_naik.gmt", "0.6p,firebrick", "Thrust fault"),
            ("sesar_turun.gmt", "0.6p,dodgerblue3", "Normal fault"),
            ("sesar_mendatar.gmt", "0.6p,purple3", "Strike-slip fault"),
            ("antiklin.gmt", "0.5p,gray15", "Anticline"),
            ("sinklin.gmt", "0.5p,gray55", "Syncline"),
        ]
        for fname, pen, label in features:
            fpath = tdir / fname
            if fpath.exists():
                fig.plot(data=str(fpath), pen=pen, label=label)
    # Active volcanoes as red triangles (conventional symbol) if requested.
    vloc = tdir / "volcano_loc.txt"
    if volcanoes and vloc.exists():
        volc = np.loadtxt(vloc, usecols=(0, 1))
        fig.plot(x=volc[:, 0], y=volc[:, 1], style="t0.26c",
                 fill="red2", pen="0.3p,black", label="Holocene volcano")
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
    F = C.FIGURES
    # 1) Whole Indonesia, clean (no tectonic features) — see the Moho pattern.
    plot(out=F / "moho_full_clean.png", tectonics=False, volcanoes=False,
         title="Moho depth of Indonesia (0.25 deg)")
    # 2) Western Indonesia (west .. 120E), all tectonic features.
    plot(out=F / "moho_west.png", region=(94, 120, -11, 6),
         tectonics=True, volcanoes=True, title="Moho depth — Western Indonesia")
    # 3) Eastern Indonesia (115E .. east), all tectonic features. Overlaps 115-120
    #    with the western panel so features correlate across the two maps.
    plot(out=F / "moho_east.png", region=(115, 141, -11, 6),
         tectonics=True, volcanoes=True, title="Moho depth — Eastern Indonesia")
    print("Wrote 3 panels to", F)
