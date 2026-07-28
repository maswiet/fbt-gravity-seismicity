"""
11 — Gravity disturbance.

    delta(P) = g(P) - gamma(P)                                        (paper eq. 1)

Subtract WGS84 Normal (ellipsoidal) gravity, computed at the same point with a
closed-form formula, from the observed GGM gravity. The result contains only the
effects anomalous with respect to the Normal Earth.

Input : GGM gravity grid (from step 10)
Output: config.GRID_DISTURBANCE

Run:  python moho_indonesia/11_gravity_disturbance.py
"""
from __future__ import annotations

import boule as bl

from _bootstrap import C, mu


def compute_disturbance():
    """Return the gravity disturbance grid.

    If the ICGEM grid already IS gravity_disturbance, load and pass through.
    Otherwise load observed gravity and subtract boule.WGS84 normal gravity at
    COMPUTATION_HEIGHT.

    TODO:
      - Load the raw gravity grid from config.GRAVITY_RAW.
      - ellipsoid = bl.WGS84; gamma = ellipsoid.normal_gravity(lat, height).
      - disturbance = observed - gamma  (watch units: mGal).
      - Save via mu.save_grid(..., C.GRID_DISTURBANCE, name="gravity_disturbance").
    """
    ellipsoid = bl.WGS84  # noqa: F841  (used once implemented)
    raise NotImplementedError("Compute the gravity disturbance grid.")


def main() -> None:
    C.ensure_dirs()
    compute_disturbance()
    print("Wrote", C.GRID_DISTURBANCE)


if __name__ == "__main__":
    main()
