"""
15 — Estimate the three hyperparameters (mu, z_ref, drho).

Two-step strategy from Uieda & Barbosa (2017), Section 2.6:

  Step 1 — regularization parameter mu, by HOLD-OUT CROSS-VALIDATION on the
           gravity data (paper Fig. 7a/10a). Split the sediment-free Bouguer grid
           into training/testing sets; for each mu invert on training and score
           the Mean Square Error (MSE) on testing; pick the MSE minimum.

  Step 2 — reference depth z_ref and density contrast drho, by VALIDATION against
           the seismic Moho points (Depth_Moho.txt) (paper Fig. 7b/10b). Using
           the chosen mu, invert over a grid of (z_ref, drho) and pick the pair
           whose predicted Moho best matches the seismic depths.

Writes the chosen hyperparameters to config.HYPERPARAMS_JSON.

Run:  python moho_indonesia/15_hyperparameters.py
"""
from __future__ import annotations

import json

import numpy as np  # noqa: F401

from _bootstrap import C, mu

# import the inversion core (module name starts with a digit -> load via runpy/importlib)
import importlib.util as _ilu
import pathlib as _pl
_spec = _ilu.spec_from_file_location(
    "moho_inversion", _pl.Path(__file__).with_name("14_moho_inversion.py"))
moho_inversion = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(moho_inversion)  # type: ignore


def cross_validate_mu():
    """Step 1: pick mu by hold-out cross-validation on the gravity data.

    TODO:
      - Load config.GRID_SED_FREE_BOUGUER; split points into train/test using
        verde.train_test_split (seed C.CV_RANDOM_SEED, C.CV_TEST_FRACTION).
      - For mu in C.MU_VALUES: invert on train (fixed z_ref, drho first guess),
        predict at test points, compute MSE.
      - Return the mu at the MSE minimum and the full MSE curve (for Fig. 7a).
    """
    raise NotImplementedError("Implement mu cross-validation.")


def validate_zref_drho(mu_reg: float):
    """Step 2: pick (z_ref, drho) by validation against seismic Moho points.

    TODO:
      - moho_pts = mu.load_seismic_moho().
      - For (z_ref, drho) in product(C.ZREF_VALUES, C.DRHO_VALUES): invert with
        the fixed mu_reg, sample the estimated Moho at the seismic point
        locations, compute MSE vs depth_km.
      - Return the (z_ref, drho) at the MSE minimum and the MSE surface (Fig. 7b).
    """
    raise NotImplementedError("Implement (z_ref, drho) validation.")


def main() -> None:
    C.ensure_dirs()
    best_mu = cross_validate_mu()
    best_zref, best_drho = validate_zref_drho(best_mu)
    result = {"mu": float(best_mu), "z_ref_km": float(best_zref),
              "drho": float(best_drho)}
    C.HYPERPARAMS_JSON.write_text(json.dumps(result, indent=2))
    print("Chosen hyperparameters:", result)


if __name__ == "__main__":
    main()
