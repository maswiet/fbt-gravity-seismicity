"""crossval — spatially-blocked k-fold cross-validation of the (z_ref, drho)
calibration, to show the reported seismic fit is not an artefact of tuning on the
same 105 points (reviewer F1). For each fold we pick (z_ref, drho) on the training
stations only and score the held-out stations; the pooled out-of-fold RMS is the
honest predictive error.

Reuses run_real's data preparation and the same Bott+Tikhonov invert() as
calibrate.py. Run (fbt env):  python moho_indonesia/crossval.py
"""
from __future__ import annotations

import itertools
import pathlib
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.interpolate import RegularGridInterpolator
from scipy.cluster.vq import kmeans2

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402
import run_real             # noqa: E402

SPACING = 0.5
MU = 1e-10                                   # featured (essentially unregularised)
ZREF_SET = [30.0, 32.5, 35.0, 37.5, 40.0]
DRHO_SET = [400.0, 450.0, 500.0, 550.0, 600.0]
MAX_ITER, TOL = 25, 0.15
K_FOLDS = 5
SEED = 42


def main():
    lon2d, lat2d = run_real.build_grid(SPACING)
    topo, disturbance = run_real.fetch_data(lon2d, lat2d, "30m", "faa")
    tess, dens = mu.topography_to_tesseroids(topo, lon2d, lat2d)
    bouguer = disturbance - mu.tesseroid_gravity_grid(tess, dens, lon2d, lat2d,
                                                      height_m=run_real.HEIGHT)
    obs = bouguer.ravel()
    n_lat, n_lon = bouguer.shape
    n = n_lat * n_lon
    RtR = (lambda R: (R.T @ R).tocsr())(mu.finite_difference_matrix(n_lat, n_lon))
    forward = mu.make_tesseroid_forward(lon2d, lat2d, height_m=run_real.HEIGHT)
    w = np.ones(n)

    def invert(drho, z_ref):
        a = -mu.bouguer_plate_jacobian(drho)
        solve = spla.factorized((sp.diags(a * a * w) + MU * RtR).tocsc())
        p = np.full(n, z_ref * 1000.0)
        prev = None
        for _ in range(MAX_ITER):
            pred = np.asarray(forward(p, z_ref, drho), float).ravel()
            rms = float(np.sqrt(np.mean((obs - pred) ** 2)))
            if prev is not None and abs(prev - rms) < TOL:
                break
            prev = rms
            p = np.clip(p + solve(a * (obs - pred) - MU * (RtR @ p)), 3000.0, 70000.0)
        return (p / 1000.0).reshape(n_lat, n_lon)

    seis = mu.load_seismic_moho()
    slon, slat, sdep = seis.longitude.values, seis.latitude.values, seis.depth_km.values
    pts = np.column_stack([slat, slon])

    # prediction cube: pred[i, iz, jd] = model Moho at station i for (z_ref, drho)
    grid = list(itertools.product(enumerate(ZREF_SET), enumerate(DRHO_SET)))
    cube = np.full((len(sdep), len(ZREF_SET), len(DRHO_SET)), np.nan)
    for (iz, z), (jd, d) in grid:
        moho = invert(d, z)
        gi = RegularGridInterpolator((lat2d[:, 0], lon2d[0, :]), moho,
                                     bounds_error=False, fill_value=np.nan)
        cube[:, iz, jd] = gi(pts)
        print(f"  inverted z_ref={z:.1f} drho={d:.0f}")

    def rms(mask, iz, jd):
        r = cube[mask, iz, jd] - sdep[mask]
        r = r[np.isfinite(r)]
        return np.sqrt(np.mean(r ** 2))

    # global (in-sample) optimum
    best = min(((iz, jd) for (iz, _), (jd, _) in grid),
               key=lambda k: rms(np.ones(len(sdep), bool), *k))
    insample = rms(np.ones(len(sdep), bool), *best)
    print(f"\nIn-sample optimum: z_ref={ZREF_SET[best[0]]:.1f}, "
          f"drho={DRHO_SET[best[1]]:.0f}, RMS={insample:.2f} km")

    # spatially-blocked folds via k-means on (lon, lat)
    xy = np.column_stack([slon, slat]).astype(float)
    _, labels = kmeans2(xy, K_FOLDS, seed=SEED, minit="++")
    print(f"\n{K_FOLDS}-fold spatial CV (fold picks its own z_ref,drho on TRAIN):")
    oof = []
    for f in range(K_FOLDS):
        te = labels == f
        tr = ~te
        pick = min(((iz, jd) for (iz, _), (jd, _) in grid), key=lambda k: rms(tr, *k))
        r_te = rms(te, *pick)
        oof.append((r_te, te.sum()))
        print(f"  fold {f}: n_test={te.sum():2d}  picked z_ref={ZREF_SET[pick[0]]:.1f} "
              f"drho={DRHO_SET[pick[1]]:.0f}  held-out RMS={r_te:.2f} km")
    pooled = np.sqrt(np.average([r ** 2 for r, nn in oof], weights=[nn for r, nn in oof]))
    print(f"\nPooled out-of-fold RMS = {pooled:.2f} km   (in-sample {insample:.2f} km)")
    print(f"=> optimism (out-of-fold - in-sample) = {pooled - insample:+.2f} km")


if __name__ == "__main__":
    main()
