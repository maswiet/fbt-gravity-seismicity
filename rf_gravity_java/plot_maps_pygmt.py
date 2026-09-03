"""
Publication-quality maps for the Central Java RF+gravity study, with PyGMT:
high-resolution GSHHG coastlines, a fancy map frame, and clean colour bars.
Overwrites the matplotlib PNGs in figures/rf_java/ so the deck picks them up.

Run (fbt env):  python rf_gravity_java/plot_maps_pygmt.py
"""
from __future__ import annotations

import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C

PROJ = "M17c"
STA_REGION = [109.3, 111.7, -8.45, -5.7]     # includes northern Karimunjawa arm
GRID_REGION = [109.3, 111.6, -8.4, -6.3]


def _cfg(pygmt):
    pygmt.config(MAP_FRAME_TYPE="fancy+", MAP_FRAME_PEN="1.2p,gray15",
                 MAP_FRAME_WIDTH="0.14c", FONT_TITLE="17p,Helvetica-Bold",
                 FONT_ANNOT_PRIMARY="9p,Helvetica", FONT_LABEL="11p,Helvetica-Bold",
                 MAP_TICK_LENGTH_PRIMARY="0.12c", MAP_GRID_PEN_PRIMARY="0.25p,gray70,.")


def _coast(fig, region, land=None, water=None):
    fig.coast(region=region, projection=PROJ, resolution="f",
              shorelines="1/0.5p,gray20", land=land, water=water,
              borders=["1/0.4p,gray40"])


def sediment_station_map(pygmt, sed):
    fig = pygmt.Figure(); _cfg(pygmt)
    res = sed[sed.h_sed_km > 0]
    fig.basemap(region=STA_REGION, projection=PROJ,
                frame=["WSne+tRF-derived sediment thickness — Central Java (MERAMEX)",
                       "xa0.5f0.25", "ya0.5f0.25"])
    fig.coast(region=STA_REGION, projection=PROJ, resolution="f",
              land="245/243/238", water="205/226/240",
              shorelines="1/0.5p,gray25", borders=["1/0.4p,gray55"])
    vmax = float(np.ceil(res.h_sed_km.quantile(0.95)))
    pygmt.makecpt(cmap="turbo", series=[0, vmax, 0.5], reverse=False)
    fig.plot(x=res.lon, y=res.lat, fill=res.h_sed_km, cmap=True,
             style="c0.24c", pen="0.4p,gray10")
    fig.colorbar(frame=["x+lSediment thickness", "y+lkm"],
                 position="JBC+o0c/0.9c+w9c/0.35c+h")
    fig.savefig(str(C.FIGURES / "sediment_rf_map.png"), dpi=250)
    print("Wrote sediment_rf_map.png")


def grid_map(pygmt, da, out, title, cbar, cmap, series, reverse=False,
             stations=None, region=GRID_REGION):
    fig = pygmt.Figure(); _cfg(pygmt)
    if "x" in da.dims:
        da = da.rename({"x": "lon", "y": "lat"})
    elif "longitude" in da.dims:
        da = da.rename({"longitude": "lon", "latitude": "lat"})
    pygmt.makecpt(cmap=cmap, series=series, reverse=reverse, background=True)
    fig.grdimage(grid=da, region=region, projection=PROJ, cmap=True, nan_transparent=True,
                 frame=["WSne+t" + title, "xa0.5f0.25", "ya0.5f0.25"])
    fig.coast(region=region, projection=PROJ, resolution="f",
              shorelines="1/0.6p,gray15", borders=["1/0.4p,gray45"])
    if stations is not None:
        fig.plot(x=stations.lon, y=stations.lat, style="c0.10c",
                 fill="black", pen="0.3p,white")
    fig.colorbar(frame="x+l" + cbar, position="JBC+o0c/0.9c+w9c/0.35c+h")
    fig.savefig(str(C.FIGURES / out), dpi=250)
    print("Wrote", out)


def main():
    import pygmt
    import pandas as pd
    import xarray as xr
    from scipy.ndimage import gaussian_filter

    sed = pd.read_csv(C.SEDIMENT_CSV)
    sed = sed[sed.kind.isin(["EDL", "SAM"])]

    sediment_station_map(pygmt, sed)

    boug = xr.open_dataarray(C.DATA_PROCESSED / "bouguer_cjava.nc")
    if "x" in boug.dims:
        boug = boug.rename({"x": "lon", "y": "lat"})
    grid_map(pygmt, boug, "bouguer.png",
             "GGM+WGM complete Bouguer anomaly — Central Java", "mGal",
             "turbo", [-100, 200, 20])

    # residual (same 40 km Gaussian high-pass as rf_gravity_join)
    lat = boug["lat"].values
    sig = 40.0 / (111.0 * abs(lat[1] - lat[0]))
    resid = boug.copy(data=boug.values - gaussian_filter(boug.values, sigma=sig, mode="nearest"))
    grid_map(pygmt, resid, "residual.png",
             "Residual Bouguer (40 km high-pass) — basin-scale signal", "mGal",
             "polar", [-40, 40, 10])

    sedgrid = xr.open_dataarray(C.GRID_SED_GRAV)
    vmax = float(np.ceil(np.nanpercentile(sedgrid.values, 97)))
    grid_map(pygmt, sedgrid, "sediment_constrained.png",
             "RF-constrained sediment thickness (gravity + receiver functions)",
             "km", "turbo", [0, vmax, 0.5], stations=sed)


if __name__ == "__main__":
    main()
