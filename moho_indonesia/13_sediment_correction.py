"""
13 — Sediment correction -> sediment-free Bouguer disturbance (INVERSION INPUT).

Remove the modelled gravitational effect of the CRUST1.0 sedimentary layers
(upper/middle/lower) from the Bouguer disturbance. The remainder is attributed to
the anomalous Moho relief and is the input to the inversion (paper Fig. 9a).

Input : config.GRID_BOUGUER, CRUST1.0 files (from step 10)
Output: config.GRID_SED_EFFECT, config.GRID_SED_FREE_BOUGUER

Requires the `fbt` environment (harmonica). NOTE: an inaccurate sediment model
biases the Moho estimate (paper: Amazonas/Parana basins). Document assumptions.
Run:  python moho_indonesia/13_sediment_correction.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, mu


def sediment_effect(lon2d, lat2d):
    """Sum the tesseroid gravitational effect of the three CRUST1.0 sediment layers."""
    layers = mu.load_crust1_sediments(lon2d, lat2d)
    total = np.zeros(lon2d.shape, dtype=float)
    for layer in layers:
        # Skip cells with negligible thickness to avoid degenerate tesseroids.
        thickness = layer["bottom_depth_m"] - layer["top_depth_m"]
        contrast = np.where(thickness > 1.0, layer["density_contrast"], 0.0)
        tesseroids, density = mu.layer_to_tesseroids(
            layer["top_depth_m"], layer["bottom_depth_m"],
            lon2d, lat2d, contrast)
        total += mu.tesseroid_gravity_grid(tesseroids, density, lon2d, lat2d)
    return total


def main() -> None:
    C.ensure_dirs()
    bouguer = mu.load_grid(C.GRID_BOUGUER)
    lon2d, lat2d = mu.make_grid_coordinates()

    sed_effect = sediment_effect(lon2d, lat2d)
    mu.save_grid(sed_effect, lon2d, lat2d, C.GRID_SED_EFFECT,
                 name="sediment_effect", attrs={"units": "mGal"})

    sed_free = bouguer.values - sed_effect
    mu.save_grid(sed_free, lon2d, lat2d, C.GRID_SED_FREE_BOUGUER,
                 name="sediment_free_bouguer",
                 attrs={"units": "mGal", "note": "inversion input"})
    print("Wrote", C.GRID_SED_EFFECT, "and", C.GRID_SED_FREE_BOUGUER)


if __name__ == "__main__":
    main()
