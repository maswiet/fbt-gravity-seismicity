"""
16 — Final inversion, maps, and validation figures.

With the hyperparameters from step 15, run the final inversion and produce the
paper-equivalent figures:
  - Estimated Moho depth map with geologic/tectonic provinces (Fig. 11)
  - Gravity residuals map + histogram (Fig. 12a)
  - Difference between estimated and seismic Moho, map + histogram (Fig. 12b)

Interpretation focus for Indonesia: large gravity/seismic mismatches flag
crustal/mantle density anomalies unaccounted for in the corrections — expected
along the Sunda/Banda subduction (slab not modelled) and beneath volcanic arcs.

Run:  python moho_indonesia/16_results_maps.py
"""
from __future__ import annotations

import json

import numpy as np  # noqa: F401
import pygmt  # noqa: F401

from _bootstrap import C, mu

import importlib.util as _ilu
import pathlib as _pl
_spec = _ilu.spec_from_file_location(
    "moho_inversion", _pl.Path(__file__).with_name("14_moho_inversion.py"))
moho_inversion = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(moho_inversion)  # type: ignore


def final_inversion():
    """Run the inversion with the chosen hyperparameters and save the Moho grid.

    TODO:
      - Load config.HYPERPARAMS_JSON (mu, z_ref, drho).
      - observed = mu.load_grid(C.GRID_SED_FREE_BOUGUER); lon, lat = grid coords.
      - result = moho_inversion.invert(observed, lon, lat, drho, z_ref, mu).
      - Save Moho + residual grids (trim to C.REGION before plotting).
    """
    raise NotImplementedError("Run final inversion with chosen hyperparameters.")


def plot_moho_map():
    """Fig. 11 equivalent: Moho depth map over Indonesia (PyGMT)."""
    raise NotImplementedError("Plot the Moho depth map.")


def plot_validation():
    """Fig. 12 equivalent: gravity residuals and difference-from-seismic.

    TODO:
      - Gravity residual map + histogram (mean, std).
      - Sample estimated Moho at seismic points; difference = estimate - seismic;
        map + histogram; report mean/std (cf. paper mean 1.2 km, std 6.8 km).
    """
    raise NotImplementedError("Plot residual and seismic-difference figures.")


def main() -> None:
    C.ensure_dirs()
    final_inversion()
    plot_moho_map()
    plot_validation()
    print("Figures written to", C.FIGURES)


if __name__ == "__main__":
    main()
