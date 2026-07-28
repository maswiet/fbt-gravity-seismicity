"""
12 — Topographic correction -> Bouguer disturbance.

    delta_bg(P) = delta(P) - g_topo(P)                               (paper eq. 2)

Forward-model the gravitational effect of topography and oceans with tesseroids
(spherical prisms) on a curved Earth, then subtract it from the gravity
disturbance. Continents use RHO_CRUST; oceans use the water contrast so the
water column replaces rock down to the geoid.

Input : config.GRID_DISTURBANCE, topography (from step 10)
Output: config.GRID_TOPO_EFFECT, config.GRID_BOUGUER

Run:  python moho_indonesia/12_topographic_correction.py
"""
from __future__ import annotations

import harmonica as hm  # noqa: F401  (tesseroid forward modelling)

from _bootstrap import C, mu


def topographic_effect():
    """Forward model the topo/ocean gravitational effect with tesseroids.

    TODO:
      - Build tesseroids from the topography grid: land columns density RHO_CRUST,
        ocean columns density RHO_OCEAN_CONTRAST (relative to reference).
      - g_topo = hm.tesseroid_gravity(coords, tesseroids, density, field="g_z")
        evaluated at COMPUTATION_HEIGHT over REGION_PADDED.
      - Save to config.GRID_TOPO_EFFECT.
    """
    raise NotImplementedError("Forward model the topographic effect.")


def main() -> None:
    C.ensure_dirs()
    disturbance = mu.load_grid(C.GRID_DISTURBANCE)          # noqa: F841
    topo_effect = topographic_effect()                     # noqa: F841
    # bouguer = disturbance - topo_effect ; save to C.GRID_BOUGUER
    raise NotImplementedError("Subtract topo effect and save Bouguer disturbance.")


if __name__ == "__main__":
    main()
