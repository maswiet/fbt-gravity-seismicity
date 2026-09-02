"""
23 — Edge-detection / structural-framework maps from the residual Bouguer.

All derivatives are computed on the projected metre grid (EPSG per config), then
mapped back to lat/lon. Products (each a NetCDF grid):

  THD   total horizontal derivative  — maxima trace basin flanks & faults
  TDR   tilt derivative (deg)        — zero contour maps edges; scale-independent
  ASA   analytic-signal amplitude    — peaks over source edges/contacts
  THETA theta map (THD/ASA)          — normalised edge enhancer

Optional pre-derivative upward continuation (C.PRE_DERIV_UPWARD_M) suppresses
short-wavelength noise before differentiation.

Reads GRID_RESIDUAL. Run:  python basin_tomini/23_edge_detection.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, bu


def main() -> None:
    C.ensure_dirs()
    res = bu.load_grid(C.GRID_RESIDUAL)

    # Project to a regular metre grid so the FFT operators are physically correct.
    vals, east, north, dx, dy = bu.project_grid(res, epsg=C.PROJ_EPSG)
    if np.isnan(vals).any():
        vals = np.where(np.isnan(vals), np.nanmean(vals), vals)

    if C.PRE_DERIV_UPWARD_M and C.PRE_DERIV_UPWARD_M > 0:
        vals = bu.upward_continuation(vals, dx, dy, C.PRE_DERIV_UPWARD_M)

    thd = bu.total_horizontal_derivative(vals, dx, dy)
    tdr = bu.tilt_derivative(vals, dx, dy)
    asa = bu.analytic_signal_amplitude(vals, dx, dy)
    theta = bu.theta_map(vals, dx, dy)

    # Resample each derivative from the projected (easting/northing) grid back
    # onto the original lat/lon model grid, so all products share one geometry
    # and step 24 can map them directly. The gradient magnitudes are computed on
    # the true metre grid; only the display grid is geographic.
    from pyproj import Transformer
    from scipy.interpolate import RegularGridInterpolator

    lon = res["longitude"].values
    lat = res["latitude"].values
    LON, LAT = np.meshgrid(lon, lat)
    tr = Transformer.from_crs("EPSG:4326", f"EPSG:{C.PROJ_EPSG}", always_xy=True)
    E, N = tr.transform(LON, LAT)

    def _to_latlon(data):
        interp = RegularGridInterpolator((north, east), data,
                                         bounds_error=False, fill_value=np.nan)
        return interp(np.column_stack([N.ravel(), E.ravel()])).reshape(LON.shape)

    bu.save_grid(_to_latlon(thd), LON, LAT, C.GRID_THD, "thd",
                 attrs={"units": "mGal/m", "note": "computed on EPSG:%d grid" % C.PROJ_EPSG})
    bu.save_grid(_to_latlon(tdr), LON, LAT, C.GRID_TDR, "tdr", attrs={"units": "deg"})
    bu.save_grid(_to_latlon(asa), LON, LAT, C.GRID_ASA, "asa", attrs={"units": "mGal/m"})
    bu.save_grid(_to_latlon(theta), LON, LAT, C.GRID_THETA, "theta", attrs={"units": "ratio"})
    print("Wrote edge-detection grids to", C.DATA_PROCESSED)
    print(f"  THD  max {np.nanmax(thd):.2e} mGal/m")
    print(f"  TDR  range [{np.nanmin(tdr):.1f}, {np.nanmax(tdr):.1f}] deg")
    print(f"  ASA  max {np.nanmax(asa):.2e} mGal/m")


if __name__ == "__main__":
    main()
