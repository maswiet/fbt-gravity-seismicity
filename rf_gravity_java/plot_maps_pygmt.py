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

# Holocene volcanoes (lon, lat, name) and cities for geographic context.
VOLCANOES = [
    (110.446, -7.540, "Merapi"), (110.442, -7.454, "Merbabu"),
    (110.070, -7.384, "Sumbing"), (109.992, -7.300, "Sundoro"),
    (109.920, -7.200, "Dieng"), (111.192, -7.625, "Lawu"),
    (110.330, -7.180, "Ungaran"), (110.880, -6.620, "Muria"),
]
CITIES = [
    (110.370, -7.797, "Yogyakarta"), (110.421, -6.966, "Semarang"),
    (110.828, -7.566, "Surakarta"),
]


def overlay_geo(fig, region, labels=True):
    """Red triangles = Holocene volcanoes; black squares = cities."""
    import pygmt
    vx = [v[0] for v in VOLCANOES]; vy = [v[1] for v in VOLCANOES]
    fig.plot(x=vx, y=vy, style="t0.32c", fill="red2", pen="0.6p,black",
             region=region, projection=PROJ)
    cx = [c[0] for c in CITIES]; cy = [c[1] for c in CITIES]
    fig.plot(x=cx, y=cy, style="s0.24c", fill="white", pen="1.0p,black",
             region=region, projection=PROJ)
    if labels:
        for lon, lat, nm in VOLCANOES:
            fig.text(x=lon, y=lat + 0.06, text=nm, font="7p,Helvetica-Bold,red3",
                     justify="CB", fill="white@30", region=region, projection=PROJ)
        for lon, lat, nm in CITIES:
            fig.text(x=lon, y=lat - 0.07, text=nm, font="9p,Helvetica-Bold,black",
                     justify="CT", fill="white@20", region=region, projection=PROJ)


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
    overlay_geo(fig, STA_REGION, labels=True)
    fig.colorbar(frame=["x+lSediment thickness", "y+lkm"],
                 position="JBC+o0c/0.9c+w9c/0.35c+h")
    fig.savefig(str(C.FIGURES / "sediment_rf_map.png"), dpi=250)
    print("Wrote sediment_rf_map.png")


def grid_map(pygmt, da, out, title, cbar, cmap, series, reverse=False,
             stations=None, region=GRID_REGION, geo_labels=True):
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
    overlay_geo(fig, region, labels=geo_labels)
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
             "turbo", [-100, 200, 20], geo_labels=False)

    # residual (same 40 km Gaussian high-pass as rf_gravity_join)
    lat = boug["lat"].values
    sig = 40.0 / (111.0 * abs(lat[1] - lat[0]))
    resid = boug.copy(data=boug.values - gaussian_filter(boug.values, sigma=sig, mode="nearest"))
    grid_map(pygmt, resid, "residual.png",
             "Residual Bouguer (40 km high-pass) — basin-scale signal", "mGal",
             "polar", [-40, 40, 10], geo_labels=False)

    sedgrid = xr.open_dataarray(C.GRID_SED_GRAV)
    vmax = float(np.ceil(np.nanpercentile(sedgrid.values, 97)))
    grid_map(pygmt, sedgrid, "sediment_constrained.png",
             "RF-constrained sediment thickness (gravity + receiver functions)",
             "km", "turbo", [0, vmax, 0.5], stations=sed)


if __name__ == "__main__":
    main()
