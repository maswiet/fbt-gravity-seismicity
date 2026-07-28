"""
11 — Gravity disturbance.

    delta(P) = g(P) - gamma(P)                                        (paper eq. 1)

If the ICGEM grid already provides `gravity_disturbance`, use it directly.
Otherwise subtract WGS84 Normal (ellipsoidal) gravity, computed with a closed-form
formula at COMPUTATION_HEIGHT, from the observed GGM gravity.

Input : ICGEM .gdf grid (from step 10) in config.GRAVITY_RAW
Output: config.GRID_DISTURBANCE

Requires the `fbt` environment (harmonica, boule).
Run:  python moho_indonesia/11_gravity_disturbance.py
"""
from __future__ import annotations

import glob

import numpy as np

from _bootstrap import C, mu


def _find_gdf() -> str:
    matches = sorted(glob.glob(str(C.GRAVITY_RAW / "*.gdf")))
    if not matches:
        raise FileNotFoundError(
            f"No ICGEM .gdf found in {C.GRAVITY_RAW}. Run step 10 first.")
    return matches[0]


def compute_disturbance():
    """Return the gravity disturbance grid (2D, mGal) and its coordinates."""
    import boule as bl
    import harmonica as hm

    dataset = hm.load_icgem_gdf(_find_gdf())
    longitude = dataset.longitude.values
    latitude = dataset.latitude.values
    lon2d, lat2d = np.meshgrid(longitude, latitude)

    if "gravity_disturbance" in dataset:
        disturbance = dataset["gravity_disturbance"].values
    else:
        # Fall back to observed gravity minus WGS84 normal gravity.
        gravity = dataset["gravity_earth"].values
        gamma = bl.WGS84.normal_gravity(lat2d, height=C.COMPUTATION_HEIGHT)
        disturbance = gravity - gamma

    mu.save_grid(disturbance, lon2d, lat2d, C.GRID_DISTURBANCE,
                 name="gravity_disturbance",
                 attrs={"units": "mGal", "height_m": C.COMPUTATION_HEIGHT,
                        "ggm": C.GGM_NAME})
    return disturbance


def main() -> None:
    C.ensure_dirs()
    compute_disturbance()
    print("Wrote", C.GRID_DISTURBANCE)


if __name__ == "__main__":
    main()
