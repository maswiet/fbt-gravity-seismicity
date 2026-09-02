"""
24 — Publication maps for the Tomini basin-delineation study (PyGMT).

Renders the interpretation panels with high-resolution GSHHG coastlines:
  1. Complete Bouguer anomaly
  2. Residual Bouguer (regional removed) — the depocentre/high map
  3. Total horizontal derivative (THD) — edges/faults
  4. Tilt derivative (TDR) with its 0-deg contour — scale-independent edges
  5. Theta map — normalised edge enhancer

Reads the NetCDF grids from steps 21-23. Requires the fbt env (pygmt/gmt).
Run:  python basin_tomini/24_maps.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, bu


def _panel(fig, grid_path, cmap, series, title, cbar_label,
           zero_contour=False, reverse=False):
    import pygmt
    import xarray as xr

    grid = xr.open_dataarray(grid_path)
    if "longitude" in grid.dims:
        grid = grid.rename({"longitude": "lon", "latitude": "lat"})
    region = list(C.REGION)
    proj = "M14c"

    pygmt.makecpt(cmap=cmap, series=list(series), reverse=reverse,
                  background=True)
    fig.grdimage(grid=grid, region=region, projection=proj, cmap=True,
                 frame=["af", f"WSne+t{title}"], nan_transparent=True)
    if zero_contour:
        fig.grdcontour(grid=grid, levels=[0], pen="1.0p,white",
                       region=region, projection=proj)
    fig.coast(region=region, projection=proj, resolution="f",
              shorelines="1/0.5p,gray10", borders="1/0.3p,gray40")
    fig.colorbar(frame=f"xaf+l{cbar_label}",
                 position="JBC+o0c/0.8c+w10c/0.3c+h")


def make(out=None, panel="residual"):
    """Render one panel to a PNG. panel in {bouguer,residual,thd,tdr,theta}."""
    import pygmt
    pygmt.config(FONT_TITLE="15p,Helvetica-Bold", FONT_ANNOT_PRIMARY="9p",
                 MAP_FRAME_TYPE="plain", MAP_FRAME_PEN="0.8p,gray25")
    fig = pygmt.Figure()

    specs = {
        "bouguer": (C.GRID_BOUGUER, "polar", (-200, 200, 20),
                    "Complete Bouguer anomaly", "mGal", False, False),
        "residual": (C.GRID_RESIDUAL, "polar", (-60, 60, 10),
                     "Residual Bouguer anomaly", "mGal", False, False),
        "thd": (C.GRID_THD, "hot", (0, None, None),
                "Total horizontal derivative", "mGal/m", False, True),
        "tdr": (C.GRID_TDR, "polar", (-90, 90, 15),
                "Tilt derivative (0@. contour = edges)", "degrees", True, False),
        "theta": (C.GRID_THETA, "gray", (0, 1, 0.1),
                  "Theta map (THD/ASA)", "ratio", False, True),
    }
    grid_path, cmap, series, title, cbar, zc, rev = specs[panel]

    # Auto-scale open-ended series (e.g. THD) from the data.
    if series[1] is None:
        import xarray as xr
        vals = xr.open_dataarray(grid_path).values
        hi = float(np.nanpercentile(np.abs(vals), 98))
        series = (0, hi, hi / 10)

    _panel(fig, grid_path, cmap, series, title, cbar, zero_contour=zc, reverse=rev)
    out = out or (C.FIGURES / f"tomini_{panel}.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out), dpi=250)
    print("Wrote", out)


def main() -> None:
    C.ensure_dirs()
    for panel in ("bouguer", "residual", "thd", "tdr", "theta"):
        try:
            make(panel=panel)
        except FileNotFoundError as e:
            print(f"skip {panel}: {e}")


if __name__ == "__main__":
    main()
