"""resolution_test — Table S2 / GJI Table 1 recomputed at the adopted physical
Delta-rho = 400 kg/m3. For each gravity source (GOCO06S satellite disturbance vs
altimetry free-air proxy) and grid spacing (0.5 deg, 0.25 deg) it runs the same
Bott+Tikhonov inversion at (mu=1e-10, z_ref=35, drho=400) and reports the mean and
std of (estimated - seismic) at the 105 RF stations.

Run (fbt env):  python moho_indonesia/resolution_test.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402
import run_real             # noqa: E402

MU, ZREF, DRHO = 1e-10, 35.0, 400.0
MAX_ITER, TOL = 25, 0.15
COMBOS = [("ggm", 0.5, "30m"), ("faa", 0.5, "30m"),
          ("ggm", 0.25, "15m"), ("faa", 0.25, "15m")]


def run(source, spacing, resolution, seis):
    lon2d, lat2d = run_real.build_grid(spacing)
    topo, disturbance = run_real.fetch_data(lon2d, lat2d, resolution, source)
    tess, dens = mu.topography_to_tesseroids(topo, lon2d, lat2d)
    obs = (disturbance - mu.tesseroid_gravity_grid(tess, dens, lon2d, lat2d,
                                                   height_m=run_real.HEIGHT)).ravel()
    n_lat, n_lon = lon2d.shape
    n = n_lat * n_lon
    RtR = (lambda R: (R.T @ R).tocsr())(mu.finite_difference_matrix(n_lat, n_lon))
    forward = mu.make_tesseroid_forward(lon2d, lat2d, height_m=run_real.HEIGHT)
    a = -mu.bouguer_plate_jacobian(DRHO)
    solve = spla.factorized((sp.diags(np.full(n, a * a)) + MU * RtR).tocsc())
    p = np.full(n, ZREF * 1000.0)
    prev = None
    for _ in range(MAX_ITER):
        pred = np.asarray(forward(p, ZREF, DRHO), float).ravel()
        rms = float(np.sqrt(np.mean((obs - pred) ** 2)))
        if prev is not None and abs(prev - rms) < TOL:
            break
        prev = rms
        p = np.clip(p + solve(a * (obs - pred) - MU * (RtR @ p)), 3000.0, 70000.0)
    moho = (p / 1000.0).reshape(n_lat, n_lon)
    gi = RegularGridInterpolator((lat2d[:, 0], lon2d[0, :]), moho,
                                 bounds_error=False, fill_value=np.nan)
    est = gi(np.column_stack([seis.latitude.values, seis.longitude.values]))
    ok = np.isfinite(est)
    diff = est[ok] - seis.depth_km.values[ok]
    return diff.mean(), diff.std(), moho.min(), moho.max()


def main():
    seis = mu.load_seismic_moho()
    print(f"Resolution test at mu={MU:.0e}, z_ref={ZREF:.0f} km, drho={DRHO:.0f} kg/m3")
    print(f"{'source':10s} {'grid':>6s}  {'mean':>6s} {'std':>5s}   range")
    for source, spacing, res in COMBOS:
        m, s, lo, hi = run(source, spacing, res, seis)
        label = "GOCO06s" if source == "ggm" else "Altimetry"
        print(f"{label:10s} {spacing:5.2f}d  {m:+6.2f} {s:5.2f}   {lo:.0f}-{hi:.0f} km")


if __name__ == "__main__":
    main()
