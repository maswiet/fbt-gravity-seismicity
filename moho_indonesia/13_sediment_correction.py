"""
13 — Sediment correction -> sediment-free Bouguer disturbance (INVERSION INPUT).

Remove the modelled gravitational effect of sedimentary basins (CRUST1.0
upper/middle/lower layers) from the Bouguer disturbance. The remainder is
attributed to the anomalous Moho relief and is the input to the inversion
(paper Fig. 9a).

Input : config.GRID_BOUGUER, CRUST1.0 (from step 10)
Output: config.GRID_SED_EFFECT, config.GRID_SED_FREE_BOUGUER

Run:  python moho_indonesia/13_sediment_correction.py
"""
from __future__ import annotations

import harmonica as hm  # noqa: F401

from _bootstrap import C, mu


def sediment_effect():
    """Forward model the gravitational effect of the CRUST1.0 sediment layers.

    TODO:
      - For each sediment layer (upper/middle/lower), build tesseroids using the
        layer top/bottom and (layer_density - RHO_CRUST) as the contrast.
      - Sum the three layers' g_z at COMPUTATION_HEIGHT.
      - Save to config.GRID_SED_EFFECT.
    NOTE: an inaccurate sediment model biases the Moho estimate (paper found
    this in the Amazonas/Parana basins). Document assumptions clearly.
    """
    raise NotImplementedError("Forward model the sediment effect.")


def main() -> None:
    C.ensure_dirs()
    bouguer = mu.load_grid(C.GRID_BOUGUER)                  # noqa: F841
    sed_effect = sediment_effect()                         # noqa: F841
    # sed_free = bouguer - sed_effect ; save to C.GRID_SED_FREE_BOUGUER
    raise NotImplementedError("Subtract sediment effect and save sediment-free Bouguer.")


if __name__ == "__main__":
    main()
