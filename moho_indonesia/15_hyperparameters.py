"""
15 — Estimate the three hyperparameters (mu, z_ref, drho).

Two-step strategy from Uieda & Barbosa (2017), Section 2.6:

  Step 1 — regularization parameter mu, by HOLD-OUT CROSS-VALIDATION on the
           gravity data (paper Fig. 7a/10a). Grid nodes are split into training
           and testing sets; the inversion is driven only by training residuals,
           and the Mean Square Error (MSE) is scored at the held-out test nodes.
           mu is the value at the MSE minimum.

  Step 2 — reference depth z_ref and density contrast drho, by VALIDATION against
           the seismic Moho points (Depth_Moho.txt) (paper Fig. 7b/10b). Using
           the chosen mu, invert over a grid of (z_ref, drho) and pick the pair
           whose estimated Moho best matches the seismic depths.

Writes the chosen hyperparameters to config.HYPERPARAMS_JSON and saves the
MSE-curve / MSE-surface figures.

Requires the `fbt` env (harmonica) for the tesseroid forward model.
Run:  python moho_indonesia/15_hyperparameters.py
"""
from __future__ import annotations

import itertools
import json

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

from _bootstrap import C, mu


# --------------------------------------------------------------------------
# Masked inversion used by cross-validation (Bott + Tikhonov, eqs 13-15)
# --------------------------------------------------------------------------
def _masked_inversion(observed, lon, lat, drho, z_ref_km, mu_reg,
                      train_mask=None, max_iter=C.MAX_ITERATIONS,
                      tol=C.CONVERGENCE_TOL):
    """Invert using only `train_mask` nodes to drive the Bott update.

    Test nodes (mask False) are constrained only through the smoothness operator,
    so predicting their data measures generalization. Returns the Moho grid (km).
    """
    observed = np.asarray(observed, float)
    n_lat, n_lon = observed.shape
    n = n_lat * n_lon
    if train_mask is None:
        train_mask = np.ones(observed.shape, bool)
    w = train_mask.ravel().astype(float)          # 1 on training nodes

    a = -mu.bouguer_plate_jacobian(drho)   # signed: deeper Moho -> negative anomaly
    R = mu.finite_difference_matrix(n_lat, n_lon)
    RtR = (R.T @ R).tocsr()
    # A^T A is diagonal a^2 restricted to training nodes.
    lhs = sp.diags(a * a * w) + mu_reg * RtR
    solve = spla.factorized(lhs.tocsc())

    tess = mu.make_tesseroid_forward(lon, lat)
    z_ref_m = z_ref_km * 1000.0
    p = np.full(n, z_ref_m)
    obs = observed.ravel()
    prev = None
    for k in range(max_iter):
        predicted = np.asarray(tess(p, z_ref_km, drho), float).ravel()
        residual = (obs - predicted) * w          # only training residuals
        rms = float(np.sqrt(np.mean((obs - predicted)[w > 0] ** 2)))
        if prev is not None and abs(prev - rms) < tol:
            break
        prev = rms
        p = p + solve(a * residual - mu_reg * (RtR @ p))
    return (p / 1000.0).reshape(n_lat, n_lon)


def _predict_gravity(moho_km, lon, lat, drho, z_ref_km):
    tess = mu.make_tesseroid_forward(lon, lat)
    return np.asarray(tess(moho_km.ravel() * 1000.0, z_ref_km, drho), float)


# --------------------------------------------------------------------------
# Step 1 — cross-validate mu
# --------------------------------------------------------------------------
def cross_validate_mu(observed, lon, lat, drho, z_ref_km):
    rng = np.random.default_rng(C.CV_RANDOM_SEED)
    train_mask = rng.random(observed.shape) >= C.CV_TEST_FRACTION
    test = ~train_mask
    obs = np.asarray(observed, float)

    mse_curve = []
    for mu_reg in C.MU_VALUES:
        moho = _masked_inversion(obs, lon, lat, drho, z_ref_km, mu_reg, train_mask)
        pred = _predict_gravity(moho, lon, lat, drho, z_ref_km).reshape(obs.shape)
        mse_curve.append(float(np.mean((obs[test] - pred[test]) ** 2)))
    mse_curve = np.array(mse_curve)
    best_mu = float(C.MU_VALUES[int(np.argmin(mse_curve))])
    return best_mu, C.MU_VALUES, mse_curve


# --------------------------------------------------------------------------
# Step 2 — validate (z_ref, drho) against seismic Moho
# --------------------------------------------------------------------------
def _sample_grid_at_points(grid_km, lon, lat, points_lon, points_lat):
    from scipy.interpolate import RegularGridInterpolator
    interp = RegularGridInterpolator((lat[:, 0], lon[0, :]), grid_km,
                                     bounds_error=False, fill_value=np.nan)
    return interp(np.column_stack([points_lat, points_lon]))


def validate_zref_drho(observed, lon, lat, mu_reg):
    seismic = mu.load_seismic_moho()
    mse_surface = np.full((len(C.ZREF_VALUES), len(C.DRHO_VALUES)), np.nan)
    for i, z_ref_km in enumerate(C.ZREF_VALUES):
        for j, drho in enumerate(C.DRHO_VALUES):
            moho = _masked_inversion(observed, lon, lat, drho, z_ref_km, mu_reg)
            pred = _sample_grid_at_points(moho, lon, lat,
                                          seismic.longitude.values,
                                          seismic.latitude.values)
            ok = np.isfinite(pred)
            mse_surface[i, j] = np.mean((seismic.depth_km.values[ok] - pred[ok]) ** 2)
    flat = int(np.nanargmin(mse_surface))
    i, j = np.unravel_index(flat, mse_surface.shape)
    return float(C.ZREF_VALUES[i]), float(C.DRHO_VALUES[j]), mse_surface


def _plot_diagnostics(mus, mse_curve, mse_surface):
    import matplotlib.pyplot as plt
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    ax1.semilogx(mus, mse_curve, "o-")
    ax1.axvline(mus[np.argmin(mse_curve)], color="r", ls="--")
    ax1.set(xlabel="regularization μ", ylabel="test MSE (mGal²)",
            title="Step 1: cross-validation (μ)")
    im = ax2.pcolormesh(C.DRHO_VALUES, C.ZREF_VALUES, mse_surface, shading="auto")
    ax2.set(xlabel="density contrast Δρ (kg/m³)", ylabel="reference depth z_ref (km)",
            title="Step 2: validation vs seismic Moho")
    fig.colorbar(im, ax=ax2, label="MSE (km²)")
    fig.tight_layout()
    out = C.FIGURES / "hyperparameters.png"
    fig.savefig(out, dpi=150)
    print("Wrote", out)


def main() -> None:
    C.ensure_dirs()
    observed = mu.load_grid(C.GRID_SED_FREE_BOUGUER).values
    lon, lat = mu.make_grid_coordinates()

    best_mu, mus, mse_curve = cross_validate_mu(
        observed, lon, lat, drho=C.RHO_MOHO_CONTRAST, z_ref_km=30.0)
    best_zref, best_drho, mse_surface = validate_zref_drho(observed, lon, lat, best_mu)

    result = {"mu": best_mu, "z_ref_km": best_zref, "drho": best_drho}
    C.HYPERPARAMS_JSON.write_text(json.dumps(result, indent=2))
    _plot_diagnostics(mus, mse_curve, mse_surface)
    print("Chosen hyperparameters:", result)


if __name__ == "__main__":
    main()
