"""
25 — Overlay the digitized ESDM 2022 basin outlines on the residual Bouguer map.

Reads:
  data/processed/basin/bouguer_residual.nc   (step 22)
  data/external/basins_esdm_tomini.geojson   (digitize_esdm_basins.py)

Draws the residual anomaly with the basin polygons on top, labelled by number +
name + tectonic class. The map states clearly that the outlines are APPROXIMATE
(digitized from the 1:5,000,000 ESDM scan). Requires the fbt env (pygmt).

Run:  python basin_tomini/25_basin_overlay.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, bu


def main() -> None:
    import geopandas as gpd
    import pygmt
    import xarray as xr

    C.ensure_dirs()
    geojson = C.DATA_EXTERNAL / "basins_esdm_tomini.geojson"
    if not geojson.exists():
        raise FileNotFoundError(
            f"{geojson} missing — run: python basin_tomini/digitize_esdm_basins.py")

    grid = xr.open_dataarray(C.GRID_RESIDUAL)
    if "longitude" in grid.dims:
        grid = grid.rename({"longitude": "lon", "latitude": "lat"})
    gdf = gpd.read_file(geojson)

    region = list(C.REGION)
    proj = "M16c"
    fig = pygmt.Figure()
    pygmt.config(FONT_TITLE="15p,Helvetica-Bold", FONT_ANNOT_PRIMARY="9p",
                 MAP_FRAME_TYPE="plain", MAP_FRAME_PEN="0.8p,gray25")
    pygmt.makecpt(cmap="polar", series=[-60, 60, 10], background=True)
    fig.grdimage(grid=grid, region=region, projection=proj, cmap=True,
                 frame=["af", "WSne+tResidual Bouguer + cekungan ESDM 2022 (digitasi ~pendekatan)"],
                 nan_transparent=True)
    fig.coast(region=region, projection=proj, resolution="f",
              shorelines="1/0.5p,gray10", borders="1/0.3p,gray40")

    # Basin outlines: black halo + white line so they read over red/blue fill.
    for _, r in gdf.iterrows():
        geom = r.geometry
        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for p in polys:
            x, y = np.asarray(p.exterior.xy[0]), np.asarray(p.exterior.xy[1])
            fig.plot(x=x, y=y, pen="2.2p,black", region=region, projection=proj)
            fig.plot(x=x, y=y, pen="1.0p,white", region=region, projection=proj)

    # Labels at centroids (clip to region so off-window basins don't clutter).
    w, e, s, n = C.REGION
    for _, r in gdf.iterrows():
        c = r.geometry.centroid
        if not (w <= c.x <= e and s <= c.y <= n):
            continue
        fig.text(x=c.x, y=c.y, text=f"{r['number']} {r['name']}",
                 font="8p,Helvetica-Bold,white", fill="black@30", pen=None,
                 region=region, projection=proj)

    fig.colorbar(frame="xaf+lmGal", position="JBC+o0c/0.8c+w11c/0.3c+h")
    out = C.FIGURES / "tomini_residual_basins.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=250)
    print("Wrote", out)


if __name__ == "__main__":
    main()
