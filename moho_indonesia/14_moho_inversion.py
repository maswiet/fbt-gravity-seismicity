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
    solves the constant sparse system (eq. 13):
        [A^T A + mu R^T R] dp^k = A^T [d_obs - d(p^k)] - mu R^T R p^k
    which factors as  [a^2 I + mu R^T R] dp^k = a r^k - mu R^T R p^k.
  - Update p^{k+1} = p^k + dp^k until the data misfit stabilises.

The forward model is injectable (`forward_fn`) so the algorithm can be unit-
tested with a cheap linear forward (numpy only), then run for real with tesseroids.

Run:
    python moho_indonesia/14_moho_inversion.py --selftest   # synthetic check
    python moho_indonesia/14_moho_inversion.py              # real run (needs data)
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from _bootstrap import C, mu


@dataclass
class InversionResult:
    moho_depth_km: np.ndarray      # estimated Moho depth grid (n_lat, n_lon)
    predicted: np.ndarray          # predicted gravity at convergence (1D, mGal)
    residual: np.ndarray           # observed - predicted (1D, mGal)
    misfit_history: list           # RMS misfit per iteration (mGal)
    n_iterations: int


def invert(observed, longitude, latitude,
           drho=C.RHO_MOHO_CONTRAST,
           z_ref_km=30.0,
           mu_reg=1e-6,
           forward_fn=None,
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
    forward_fn : callable p_metres(1D) -> predicted gravity (1D, mGal). If None,
        a tesseroid forward model is built (requires harmonica + boule).
    """
    observed = np.asarray(observed, dtype=float)
    n_lat, n_lon = observed.shape
    n_params = n_lat * n_lon

    a = mu.bouguer_plate_jacobian(drho)                 # mGal per metre (eq. 15)
    R = mu.finite_difference_matrix(n_lat, n_lon)       # (n_edges, n_params)
    RtR = (R.T @ R).tocsr()

    # LHS is constant across iterations -> factorise once.
    lhs = sp.identity(n_params, format="csr") * (a * a) + mu_reg * RtR
    solve = spla.factorized(lhs.tocsc())

    z_ref_m = z_ref_km * 1000.0
    p = np.full(n_params, z_ref_m)                      # start flat at z_ref
    obs = observed.ravel()

    if forward_fn is None:
        tess = mu.make_tesseroid_forward(longitude, latitude)
        def forward_fn(p_m):                            # noqa: E306
            return tess(p_m, z_ref_km, drho)

    misfit_history: list[float] = []
    predicted = np.zeros_like(obs)
    residual = obs.copy()
    n_iter = 0
    for k in range(max_iter):
        predicted = np.asarray(forward_fn(p), dtype=float).ravel()
        residual = obs - predicted
        rms = float(np.sqrt(np.mean(residual ** 2)))
        misfit_history.append(rms)
        n_iter = k + 1
        if k > 0 and abs(misfit_history[-2] - rms) < tol:
            break
        rhs = a * residual - mu_reg * (RtR @ p)
        p = p + solve(rhs)

    moho_km = (p / 1000.0).reshape(n_lat, n_lon)
    return InversionResult(moho_km, predicted, residual, misfit_history, n_iter)


# --------------------------------------------------------------------------
# Synthetic self-test (numpy/scipy only — no harmonica, no downloads)
# --------------------------------------------------------------------------
def _self_test() -> None:
    """Recover a known Moho from Bouguer-plate synthetic data + noise."""
    rng = np.random.default_rng(0)
    n_lat, n_lon = 25, 30
    drho, z_ref_km = 400.0, 30.0
    lon, lat = np.meshgrid(np.linspace(100, 106, n_lon),
                           np.linspace(-4, 2, n_lat))

    # True Moho: reference depth + two smooth Gaussian roots (km).
    bump = (8.0 * np.exp(-(((lon - 103) ** 2 + (lat + 1) ** 2) / 2.0))
            + 4.0 * np.exp(-(((lon - 101) ** 2 + (lat - 1) ** 2) / 1.0)))
    true_moho_km = z_ref_km + bump                      # ~30..38 km
    z_ref_m = z_ref_km * 1000.0

    a = mu.bouguer_plate_jacobian(drho)
    clean = a * (true_moho_km.ravel() * 1000.0 - z_ref_m)
    obs = (clean + rng.normal(0.0, 0.5, clean.shape)).reshape(n_lat, n_lon)

    def forward(p_m):
        return mu.forward_gravity_bouguer_plate(p_m, z_ref_m, drho)

    result = invert(obs, lon, lat, drho=drho, z_ref_km=z_ref_km,
                    mu_reg=1e-5, forward_fn=forward, max_iter=30, tol=1e-3)

    err = result.moho_depth_km - true_moho_km
    rms_err = float(np.sqrt(np.mean(err ** 2)))
    print(f"[selftest] iterations         : {result.n_iterations}")
    print(f"[selftest] final data misfit  : {result.misfit_history[-1]:.4f} mGal")
    print(f"[selftest] Moho recovery RMS  : {rms_err:.4f} km "
          f"(max |err| = {np.abs(err).max():.4f} km)")
    assert rms_err < 1.0, f"Moho recovery RMS too large: {rms_err:.3f} km"
    print("[selftest] PASSED — inversion machinery recovers the synthetic Moho.")


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
    parser = argparse.ArgumentParser(description="Moho inversion (Bott + Tikhonov).")
    parser.add_argument("--selftest", action="store_true",
                        help="Run the synthetic recovery test (no data needed).")
    args = parser.parse_args()
    if args.selftest:
        _self_test()
    else:
        main()
