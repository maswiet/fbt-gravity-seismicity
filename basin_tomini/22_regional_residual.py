"""
22 — Regional-residual separation of the Bouguer anomaly.

The Bouguer field mixes deep/broad ("regional") sources with shallow basin-scale
("residual") structure. We split them so basin depocentres and structural highs
stand out. Method is set in config (C.SEPARATION_METHOD):

    upward     regional = Bouguer continued upward by C.UPWARD_HEIGHT_M
    polynomial regional = low-order 2D polynomial trend (C.POLY_DEGREE)
    gaussian   regional = gaussian low-pass at C.GAUSSIAN_CUT_M

The RESIDUAL (Bouguer - regional) is the primary field for interpretation and
for the edge detection in step 23. Transforms run on a metre grid (projected),
then the result is mapped back to lat/lon for storage.

Reads GRID_BOUGUER. Run:  python basin_tomini/22_regional_residual.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, bu


def main() -> None:
    C.ensure_dirs()
    boug = bu.load_grid(C.GRID_BOUGUER)
    lon = boug["longitude"].values
    lat = boug["latitude"].values

    dx, dy = bu.project_spacing_m(lat, C.SPACING)
    field = boug.values
    # Fill NaNs (rare, at grid edges) with the mean so the FFT is well-defined.
    if np.isnan(field).any():
        field = np.where(np.isnan(field), np.nanmean(field), field)

    regional, residual = bu.separate_regional_residual(field, dx, dy)

    LON, LAT = np.meshgrid(lon, lat)
    bu.save_grid(regional, LON, LAT, C.GRID_REGIONAL, "bouguer_regional",
                 attrs={"units": "mGal", "method": C.SEPARATION_METHOD})
    bu.save_grid(residual, LON, LAT, C.GRID_RESIDUAL, "bouguer_residual",
                 attrs={"units": "mGal", "method": C.SEPARATION_METHOD})
    print(f"Separation '{C.SEPARATION_METHOD}':")
    print("  regional range (mGal):", float(np.min(regional)), "..", float(np.max(regional)))
    print("  residual range (mGal):", float(np.min(residual)), "..", float(np.max(residual)))
    print("Wrote", C.GRID_REGIONAL, "and", C.GRID_RESIDUAL)


if __name__ == "__main__":
    main()
