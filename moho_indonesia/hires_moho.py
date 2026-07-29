"""
hires_moho — single high-resolution inversion using the calibrated hyperparameters.

Runs one final Bott+Tikhonov inversion on a finer grid (default 0.25 deg) with the
mu/z_ref/drho already chosen by calibrate.py (read from hyperparameters.json), on
the GGM gravity path. Writes GRID_MOHO so plot_pygmt.py picks it up.

Run (fbt env):  python moho_indonesia/hires_moho.py --spacing 0.25
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402
import run_real             # noqa: E402


def main(spacing, resolution, gravity, sediments):
    w, e, s, n = C.REGION
    lon2d, lat2d = np.meshgrid(np.arange(w, e + 1e-9, spacing),
                               np.arange(s, n + 1e-9, spacing))
    print(f"Grid {lon2d.shape} ({lon2d.size} cells) @ {spacing} deg | gravity={gravity}")

    hp = json.loads(C.HYPERPARAMS_JSON.read_text())
    drho, z_ref, mu_reg = hp["drho"], hp["z_ref_km"], hp["mu"]
    print(f"Hyperparameters: mu={mu_reg:.1e}, z_ref={z_ref} km, drho={drho}")

    topo, disturbance = run_real.fetch_data(lon2d, lat2d, resolution, gravity)
    tess, dens = mu.topography_to_tesseroids(topo, lon2d, lat2d)
    topo_eff = mu.tesseroid_gravity_grid(tess, dens, lon2d, lat2d, height_m=run_real.HEIGHT)
    bouguer = disturbance - topo_eff
    if sediments:
        from calibrate import sediment_effect
        bouguer = bouguer - sediment_effect(lon2d, lat2d)
    obs = bouguer.ravel()

    # Clipped Bott + Tikhonov inversion.
    n_lat, n_lon = bouguer.shape
    npar = n_lat * n_lon
    a = -mu.bouguer_plate_jacobian(drho)
    R = mu.finite_difference_matrix(n_lat, n_lon)
    RtR = (R.T @ R).tocsr()
    lhs = sp.identity(npar, format="csr") * (a * a) + mu_reg * RtR
    solve = spla.factorized(lhs.tocsc())
    forward = mu.make_tesseroid_forward(lon2d, lat2d, height_m=run_real.HEIGHT)
    p = np.full(npar, z_ref * 1000.0)
    prev = None
    for k in range(C.MAX_ITERATIONS):
        pred = np.asarray(forward(p, z_ref, drho), float).ravel()
        rms = float(np.sqrt(np.mean((obs - pred) ** 2)))
        print(f"  iter {k+1}: RMS {rms:.2f} mGal")
        if prev is not None and abs(prev - rms) < C.CONVERGENCE_TOL:
            break
        prev = rms
        p = np.clip(p + solve(a * (obs - pred) - mu_reg * (RtR @ p)), 3000.0, 70000.0)
    moho = (p / 1000.0).reshape(n_lat, n_lon)

    mu.save_grid(moho, lon2d, lat2d, C.GRID_MOHO, name="moho_depth",
                 attrs={"units": "km", "spacing_deg": spacing, "gravity": gravity,
                        "mu": mu_reg, "z_ref_km": z_ref, "drho": drho})
    # Report vs seismic.
    from scipy.interpolate import RegularGridInterpolator
    seis = mu.load_seismic_moho()
    interp = RegularGridInterpolator((lat2d[:, 0], lon2d[0, :]), moho,
                                     bounds_error=False, fill_value=np.nan)
    est = interp(np.column_stack([seis.latitude, seis.longitude]))
    ok = np.isfinite(est)
    diff = est[ok] - seis.depth_km.values[ok]
    print(f"Moho {moho.min():.1f}..{moho.max():.1f} km | diff vs seismic: "
          f"mean {diff.mean():.2f} km, std {diff.std():.2f} km")
    print("Wrote", C.GRID_MOHO)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--spacing", type=float, default=0.25)
    ap.add_argument("--resolution", default="15m")
    ap.add_argument("--gravity", choices=["faa", "ggm"], default="ggm")
    ap.add_argument("--sediments", action="store_true")
    a = ap.parse_args()
    main(a.spacing, a.resolution, a.gravity, a.sediments)
