"""
12 — Topographic correction -> Bouguer disturbance.

    delta_bg(P) = delta(P) - g_topo(P)                               (paper eq. 2)

Forward-model the gravitational effect of topography and oceans with tesseroids
(land density 2670, ocean contrast ~ -1640), then subtract it from the gravity
disturbance.

Input : config.GRID_DISTURBANCE, topography grid (from step 10)
Output: config.GRID_TOPO_EFFECT, config.GRID_BOUGUER

Requires the `fbt` environment (harmonica, boule).
Run:  python moho_indonesia/12_topographic_correction.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, mu

TOPO_GRID = C.TOPOGRAPHY_RAW / "topography.nc"   # produced by step 10


def load_topography_on_model_grid(lon2d, lat2d):
    """Load topography and interpolate onto the model grid (metres, +up)."""
    topo = mu.load_grid(TOPO_GRID)
    interp = topo.interp(
        longitude=("points", lon2d.ravel()),
        latitude=("points", lat2d.ravel()),
    )
    return np.asarray(interp.values).reshape(lon2d.shape)


def main() -> None:
    C.ensure_dirs()
    disturbance = mu.load_grid(C.GRID_DISTURBANCE)
    lon2d, lat2d = mu.make_grid_coordinates()

    topo_m = load_topography_on_model_grid(lon2d, lat2d)
    tesseroids, density = mu.topography_to_tesseroids(topo_m, lon2d, lat2d)
    topo_effect = mu.tesseroid_gravity_grid(tesseroids, density, lon2d, lat2d)
    mu.save_grid(topo_effect, lon2d, lat2d, C.GRID_TOPO_EFFECT,
                 name="topographic_effect", attrs={"units": "mGal"})

    bouguer = disturbance.values - topo_effect
    mu.save_grid(bouguer, lon2d, lat2d, C.GRID_BOUGUER,
                 name="bouguer_disturbance", attrs={"units": "mGal"})
    print("Wrote", C.GRID_TOPO_EFFECT, "and", C.GRID_BOUGUER)


if __name__ == "__main__":
    main()
