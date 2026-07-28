"""
14 — Nonlinear Moho inversion (Bott's method + Tikhonov, tesseroids).

Core of the replication. Reimplements the Uieda & Barbosa (2017) inversion on
top of Harmonica's tesseroid forward modelling (modern Fatiando has no built-in
Bott/Moho inversion class).

Method (paper Section 2.5, eqs 13-15):
  - Model the anomalous Moho as juxtaposed tesseroids; parameters = Moho depths.
  - Gauss-Newton with the Jacobian approximated by the diagonal Bouguer plate
    value  A = 2*pi*G*drho*I  (eq. 15) -> A^T A is diagonal, computed once.
  - Regularise with first-order Tikhonov smoothness R (eq. 9). Each iteration
    solves the sparse system (eq. 13):
        [A^T A + mu R^T R] dp^k = A^T [d_obs - d(p^k)] - mu R^T R p^k
  - Update p^{k+1} = p^k + dp^k until the data misfit stabilises.

This module exposes `invert()` so 15_hyperparameters.py can call it in loops.

Run (single inversion with config defaults):
    python moho_indonesia/14_moho_inversion.py
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla  # noqa: F401  (sparse solve)

from _bootstrap import C, mu


@dataclass
class InversionResult:
    moho_depth_km: np.ndarray      # estimated Moho depth grid (n_lat, n_lon)
    predicted: np.ndarray          # predicted gravity at convergence
    residual: np.ndarray           # observed - predicted
    misfit_history: list           # RMS misfit per iteration
    n_iterations: int


def invert(observed, longitude, latitude,
           drho=C.RHO_MOHO_CONTRAST,
           z_ref_km=30.0,
           mu_reg=1e-6,
           max_iter=C.MAX_ITERATIONS,
           tol=C.CONVERGENCE_TOL) -> InversionResult:
    """Estimate Moho depths from the sediment-free Bouguer disturbance.

    Parameters
    ----------
    observed : 2D array (mGal) — the inversion input (step 13 output).
    longitude, latitude : 2D grids matching `observed`.
    drho : Moho density contrast (kg/m^3).
    z_ref_km : reference (Normal-Earth) Moho depth (km).
    mu_reg : Tikhonov regularization parameter.

    Returns
    -------
    InversionResult
    """
    n_lat, n_lon = observed.shape
    n_params = n_lat * n_lon

    # Diagonal Jacobian value (scalar) and roughness operator.
    a = mu.bouguer_plate_jacobian(drho)                 # mGal per metre (eq. 15)
    R = mu.finite_difference_matrix(n_lat, n_lon)       # (n_edges, n_params)
    RtR = (R.T @ R).tocsr()

    # Left-hand-side matrix is constant across iterations (A^T A diagonal + mu R^T R).
    lhs = sp.identity(n_params, format="csr") * (a * a) + mu_reg * RtR

    # Initial model: flat Moho at the reference depth (paper starts at z_ref).
    p = np.full(n_params, z_ref_km * 1000.0)            # metres, positive down
    obs = observed.ravel()
    misfit_history: list[float] = []

    for k in range(max_iter):
        # --- forward model gravity of the current Moho ---
        # TODO: predicted = forward_gravity(p, longitude, latitude, z_ref_km, drho)
        #       via mu.moho_to_tesseroids(...) + harmonica.tesseroid_gravity.
        raise NotImplementedError("Wire forward modelling into the iteration.")

        # residual = obs - predicted
        # rms = sqrt(mean(residual**2)); misfit_history.append(rms)
        # rhs = a * residual - mu_reg * (RtR @ p)
        # dp = spla.spsolve(lhs, rhs)
        # p = p + dp
        # if k > 0 and abs(misfit_history[-2] - rms) < tol: break

    moho_km = p.reshape(n_lat, n_lon) / 1000.0           # noqa: F841
    raise NotImplementedError("Assemble and return InversionResult.")


def main() -> None:
    C.ensure_dirs()
    observed = mu.load_grid(C.GRID_SED_FREE_BOUGUER)
    lon, lat = mu.make_grid_coordinates()
    result = invert(observed.values, lon, lat)
    mu.save_grid(result.moho_depth_km, lon, lat, C.GRID_MOHO,
                 name="moho_depth", attrs={"units": "km", "positive": "down"})
    mu.save_grid(result.residual.reshape(observed.shape), lon, lat,
                 C.GRID_GRAVITY_RESIDUAL, name="gravity_residual",
                 attrs={"units": "mGal"})
    print(f"Converged in {result.n_iterations} iterations; "
          f"final RMS = {result.misfit_history[-1]:.3f} mGal")


if __name__ == "__main__":
    main()
