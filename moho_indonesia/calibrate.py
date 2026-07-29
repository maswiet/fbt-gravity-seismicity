"""
calibrate — step 15 on the REAL coarse data: estimate mu, z_ref, drho.

Two-step (Uieda & Barbosa 2017 sec 2.6):
  1. mu by hold-out cross-validation on the (real) sediment-free Bouguer grid.
  2. (z_ref, drho) by validation against the 105 seismic Moho points.

Reuses run_real's data preparation (earth_relief + earth_faa -> Bouguer), then
re-runs the final inversion with the chosen hyperparameters and rewrites the
Moho grid so plot_pygmt.py picks up the calibrated result.

Run (fbt env):  python moho_indonesia/calibrate.py
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402
import run_real             # noqa: E402  (reuse build_grid, fetch_data, HEIGHT)

SPACING = 0.5
MU_SET = np.logspace(-10, -4, 4)              # 1e-10 .. 1e-4
ZREF_SET = [25.0, 30.0, 35.0, 40.0]           # km
DRHO_SET = [300.0, 400.0, 500.0]              # kg/m^3
MAX_ITER = 25
TOL = 0.15


def sediment_effect(lon2d, lat2d):
    """Tesseroid gravitational effect (mGal) of the CRUST1.0 sediment layers."""
    layers = mu.load_crust1_sediments(lon2d, lat2d)
    eff = np.zeros(lon2d.shape)
    for L in layers:
        thick = L["bottom_depth_m"] - L["top_depth_m"]
        contrast = np.where(thick > 1.0, L["density_contrast"], 0.0)
        t, d = mu.layer_to_tesseroids(L["top_depth_m"], L["bottom_depth_m"],
                                      lon2d, lat2d, contrast)
        eff += mu.tesseroid_gravity_grid(t, d, lon2d, lat2d, height_m=run_real.HEIGHT)
    return eff


def main(gravity_source="faa", sediments=False):
    lon2d, lat2d = run_real.build_grid(SPACING)
    print(f"Grid {lon2d.shape} ({lon2d.size} cells) @ {SPACING} deg | "
          f"gravity={gravity_source} | sediments={sediments}")
    topo, disturbance = run_real.fetch_data(lon2d, lat2d, "30m", gravity_source)

    tess, dens = mu.topography_to_tesseroids(topo, lon2d, lat2d)
    topo_eff = mu.tesseroid_gravity_grid(tess, dens, lon2d, lat2d, height_m=run_real.HEIGHT)
    bouguer = disturbance - topo_eff
    if sediments:
        sed_eff = sediment_effect(lon2d, lat2d)
        print(f"Sediment effect: {sed_eff.min():.0f}..{sed_eff.max():.0f} mGal (removed)")
        sed_free = bouguer - sed_eff
    else:
        sed_free = bouguer
    obs = sed_free.ravel()

    n_lat, n_lon = sed_free.shape
    n = n_lat * n_lon
    R = mu.finite_difference_matrix(n_lat, n_lon)
    RtR = (R.T @ R).tocsr()
    forward = mu.make_tesseroid_forward(lon2d, lat2d, height_m=run_real.HEIGHT)

    def invert(drho, z_ref, mu_reg, w):
        """Masked Bott+Tikhonov inversion; w=1 on nodes that drive the update.

        Moho depths are clipped to a physical range each iteration so the model
        never overshoots to negative depth (which would place a tesseroid above
        the computation height and make the forward unreliable).
        """
        a = -mu.bouguer_plate_jacobian(drho)
        lhs = sp.diags(a * a * w) + mu_reg * RtR
        solve = spla.factorized(lhs.tocsc())
        p = np.full(n, z_ref * 1000.0)
        prev = None
        for _ in range(MAX_ITER):
            pred = np.asarray(forward(p, z_ref, drho), float).ravel()
            resid = (obs - pred) * w
            rms = float(np.sqrt(np.mean((obs - pred)[w > 0] ** 2)))
            if prev is not None and abs(prev - rms) < TOL:
                break
            prev = rms
            p = np.clip(p + solve(a * resid - mu_reg * (RtR @ p)), 3000.0, 70000.0)
        return (p / 1000.0).reshape(n_lat, n_lon)

    # ---- Step 1: cross-validate mu -----------------------------------------
    print("\n[Step 1] mu cross-validation (z_ref=30, drho=400):")
    rng = np.random.default_rng(C.CV_RANDOM_SEED)
    train = rng.random(sed_free.shape) >= C.CV_TEST_FRACTION
    test = ~train
    w_tr = train.ravel().astype(float)
    best_mu, best = MU_SET[0], np.inf
    for m in MU_SET:
        moho = invert(400.0, 30.0, m, w_tr)
        pred = np.asarray(forward(moho.ravel() * 1000.0, 30.0, 400.0),
                          float).reshape(sed_free.shape)
        mse = float(np.mean((sed_free[test] - pred[test]) ** 2))
        print(f"   mu={m:.1e}  testMSE={mse:8.2f}")
        if mse < best:
            best, best_mu = mse, m

    # ---- Step 2: validate (z_ref, drho) vs seismic Moho --------------------
    print(f"\n[Step 2] (z_ref, drho) validation vs seismic (mu={best_mu:.1e}):")
    seis = mu.load_seismic_moho()
    w_full = np.ones(n)
    best_pair, best_mse = (30.0, 400.0), np.inf
    for z, d in itertools.product(ZREF_SET, DRHO_SET):
        moho = invert(d, z, best_mu, w_full)
        interp = RegularGridInterpolator((lat2d[:, 0], lon2d[0, :]), moho,
                                         bounds_error=False, fill_value=np.nan)
        est = interp(np.column_stack([seis.latitude, seis.longitude]))
        ok = np.isfinite(est)
        mse = float(np.mean((seis.depth_km.values[ok] - est[ok]) ** 2))
        print(f"   z_ref={z:.0f} drho={d:.0f}  seisRMS={np.sqrt(mse):5.2f} km")
        if mse < best_mse:
            best_mse, best_pair = mse, (z, d)
    z_ref, drho = best_pair

    # ---- Final calibrated inversion + save ---------------------------------
    moho = invert(drho, z_ref, best_mu, w_full)
    mu.save_grid(moho, lon2d, lat2d, C.GRID_MOHO, name="moho_depth",
                 attrs={"units": "km", "spacing_deg": SPACING,
                        "mu": best_mu, "z_ref_km": z_ref, "drho": drho,
                        "note": "calibrated v1 (faa proxy, no sediments)"})
    hp = {"mu": float(best_mu), "z_ref_km": float(z_ref), "drho": float(drho)}
    C.HYPERPARAMS_JSON.write_text(json.dumps(hp, indent=2))

    interp = RegularGridInterpolator((lat2d[:, 0], lon2d[0, :]), moho,
                                     bounds_error=False, fill_value=np.nan)
    est = interp(np.column_stack([seis.latitude, seis.longitude]))
    ok = np.isfinite(est)
    diff = est[ok] - seis.depth_km.values[ok]
    print(f"\nCALIBRATED: mu={best_mu:.1e}, z_ref={z_ref:.0f} km, drho={drho:.0f}")
    print(f"Moho range {moho.min():.1f}..{moho.max():.1f} km")
    print(f"Difference vs {ok.sum()} seismic points: "
          f"mean {diff.mean():.2f} km, std {diff.std():.2f} km "
          f"(was mean -4.55, std 6.27 uncalibrated)")
    print("Wrote", C.GRID_MOHO, "and", C.HYPERPARAMS_JSON)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gravity", choices=["faa", "ggm"], default="faa")
    ap.add_argument("--sediments", action="store_true",
                    help="Remove the CRUST1.0 sediment effect before inversion.")
    args = ap.parse_args()
    main(args.gravity, args.sediments)
