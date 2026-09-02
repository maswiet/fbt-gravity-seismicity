"""
Analysis on the user-supplied GGM+WGM Bouguer anomaly (professional 500 m grid)
as an INDEPENDENT alternative to the Sandwell-derived pipeline (steps 20-25).

Input : data/external/ggm_wgm/bouguer_ggmwgm_tomini.nc
        (reprojected from the ESDM/Geosoft GXF: EPSG:3857 -> WGS84, 0.005 deg,
         region 119-126E, -2.5..2.5; see README).
Steps : regional-residual separation + edge detection (THD, TDR) at native
        spacing, then Bouguer / residual / residual+basins / TDR maps.

Run:  python basin_tomini/ggmwgm_analysis.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, bu

SRC = C.DATA_EXTERNAL / "ggm_wgm" / "bouguer_ggmwgm_tomini.nc"
TAG = "ggmwgm"


def _load():
    import xarray as xr
    da = xr.open_dataarray(SRC)
    ren = {}
    for c in da.dims:
        if c in ("lon", "x"):
            ren[c] = "longitude"
        elif c in ("lat", "y"):
            ren[c] = "latitude"
    da = da.rename(ren) if ren else da
    if da["latitude"][0] > da["latitude"][-1]:
        da = da.sortby("latitude")
    return da


def main():
    import geopandas as gpd
    import pygmt
    import xarray as xr

    C.ensure_dirs()
    boug = _load()
    lon = boug["longitude"].values
    lat = boug["latitude"].values
    spacing = float(abs(lon[1] - lon[0]))
    field = bu.fill_nan_nearest(boug.values)
    dx, dy = bu.project_spacing_m(lat, spacing)

    # Regional-residual (same method as step 22) + edge detection (step 23).
    regional, residual = bu.separate_regional_residual(field, dx, dy)
    LON, LAT = np.meshgrid(lon, lat)
    res_da = bu.save_grid(residual, LON, LAT,
                          C.DATA_PROCESSED / f"bouguer_residual_{TAG}.nc",
                          "bouguer_residual", attrs={"units": "mGal",
                          "source": "GGM+WGM", "separation": C.SEPARATION_METHOD})
    tdr = bu.tilt_derivative(field if False else residual, dx, dy)
    bu.save_grid(tdr, LON, LAT, C.DATA_PROCESSED / f"tdr_{TAG}.nc", "tdr",
                 attrs={"units": "deg"})
    print(f"GGM+WGM @ {spacing:.4f} deg | Bouguer [{field.min():.0f},{field.max():.0f}] "
          f"| residual [{residual.min():.0f},{residual.max():.0f}] mGal")

    # ---- Maps -------------------------------------------------------------
    geojson = C.DATA_EXTERNAL / "basins_esdm_tomini.geojson"
    gdf = gpd.read_file(geojson) if geojson.exists() else None
    region = list(C.REGION)
    proj = "M16c"

    def basemap(fig, grid, series, cmap, title, cbar):
        pygmt.makecpt(cmap=cmap, series=series, background=True)
        fig.grdimage(grid=grid, region=region, projection=proj, cmap=True,
                     frame=["af", f"WSne+t{title}"], nan_transparent=True)
        fig.coast(region=region, projection=proj, resolution="f",
                  shorelines="1/0.5p,gray10", borders="1/0.3p,gray40")
        fig.colorbar(frame=f"xaf+l{cbar}", position="JBC+o0c/0.8c+w11c/0.3c+h")

    def add_basins(fig, labels=True):
        if gdf is None:
            return
        w, e, s, n = C.REGION
        for _, r in gdf.iterrows():
            g = r.geometry
            for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
                x, y = np.asarray(p.exterior.xy[0]), np.asarray(p.exterior.xy[1])
                fig.plot(x=x, y=y, pen="2.2p,black", region=region, projection=proj)
                fig.plot(x=x, y=y, pen="1.0p,white", region=region, projection=proj)
            c = g.centroid
            if labels and w <= c.x <= e and s <= c.y <= n:
                fig.text(x=c.x, y=c.y, text=f"{r['number']} {r['name']}",
                         font="8p,Helvetica-Bold,white", fill="black@30",
                         region=region, projection=proj)

    pygmt.config(FONT_TITLE="14p,Helvetica-Bold", FONT_ANNOT_PRIMARY="9p",
                 MAP_FRAME_TYPE="plain", MAP_FRAME_PEN="0.8p,gray25")

    # 1) Bouguer
    fig = pygmt.Figure()
    basemap(fig, boug.rename({"longitude": "lon", "latitude": "lat"}),
            [-160, 160, 20], "polar", "GGM+WGM Bouguer anomaly (500 m)", "mGal")
    fig.savefig(str(C.FIGURES / f"tomini_bouguer_{TAG}.png"), dpi=250)

    # 2) Residual + basins
    fig = pygmt.Figure()
    basemap(fig, res_da.rename({"longitude": "lon", "latitude": "lat"}),
            [-40, 40, 5], "polar",
            "GGM+WGM residual Bouguer + cekungan ESDM (digitasi ~pendekatan)", "mGal")
    add_basins(fig)
    fig.savefig(str(C.FIGURES / f"tomini_residual_basins_{TAG}.png"), dpi=250)

    # 3) TDR + basins (edges)
    tdr_da = xr.open_dataarray(C.DATA_PROCESSED / f"tdr_{TAG}.nc")
    fig = pygmt.Figure()
    basemap(fig, tdr_da.rename({"longitude": "lon", "latitude": "lat"}),
            [-90, 90, 15], "polar", "GGM+WGM tilt derivative (tepi struktur)", "deg")
    add_basins(fig, labels=False)
    fig.savefig(str(C.FIGURES / f"tomini_tdr_{TAG}.png"), dpi=250)

    print("Wrote maps:", C.FIGURES / f"tomini_bouguer_{TAG}.png", "and 2 more")


if __name__ == "__main__":
    main()
