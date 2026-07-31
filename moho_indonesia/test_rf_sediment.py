"""
test_rf_sediment — does the RF (Bahri) western-Indonesia sediment thickness change
the Moho model? Interpolates the 91 RF sediment-thickness points onto the grid,
computes their tesseroid gravity effect, removes it, re-inverts, and compares to
the no-RF-sediment baseline (seismic fit, Moho difference).

Run (fbt env):  python moho_indonesia/test_rf_sediment.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.interpolate import RegularGridInterpolator, griddata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402
import run_real             # noqa: E402

SED_DENSITY = 2320.0        # assumed sediment density (kg/m^3); contrast vs 2670


def invert(obs, lon2d, lat2d, drho, z_ref, mu_reg, forward, RtR, n_lat, n_lon):
    a = -mu.bouguer_plate_jacobian(drho)
    lhs = sp.identity(n_lat * n_lon, format="csr") * (a * a) + mu_reg * RtR
    solve = spla.factorized(lhs.tocsc())
    p = np.full(n_lat * n_lon, z_ref * 1000.0)
    prev = None
    o = obs.ravel()
    for _ in range(25):
        pred = np.asarray(forward(p, z_ref, drho), float).ravel()
        rms = float(np.sqrt(np.mean((o - pred) ** 2)))
        if prev is not None and abs(prev - rms) < 0.15:
            break
        prev = rms
        p = np.clip(p + solve(a * (o - pred) - mu_reg * (RtR @ p)), 3000.0, 70000.0)
    return (p / 1000.0).reshape(n_lat, n_lon)


def main():
    hp = json.loads(C.HYPERPARAMS_JSON.read_text())
    drho, z_ref, mu_reg = hp["drho"], hp["z_ref_km"], hp["mu"]
    lon2d, lat2d = run_real.build_grid(0.5)
    n_lat, n_lon = lon2d.shape
    topo, disturbance = run_real.fetch_data(lon2d, lat2d, "30m", "ggm")
    tess, dens = mu.topography_to_tesseroids(topo, lon2d, lat2d)
    topo_eff = mu.tesseroid_gravity_grid(tess, dens, lon2d, lat2d, height_m=run_real.HEIGHT)
    bouguer = disturbance - topo_eff
    R = mu.finite_difference_matrix(n_lat, n_lon); RtR = (R.T @ R).tocsr()
    forward = mu.make_tesseroid_forward(lon2d, lat2d, height_m=run_real.HEIGHT)

    # RF sediment thickness -> grid (linear within hull, 0 outside).
    rf = np.genfromtxt(C.DATA_EXTERNAL / "rf_sediment_moho_bahri.txt",
                       names=True, dtype=None, encoding="utf-8")
    sed_km = griddata((rf["lon"], rf["lat"]), rf["sed_km"],
                      (lon2d, lat2d), method="linear", fill_value=0.0)
    sed_km = np.nan_to_num(sed_km, nan=0.0)
    print(f"RF sediment on grid: 0..{sed_km.max():.1f} km (mean {sed_km.mean():.2f})")

    # Sediment tesseroid effect (top=0, bottom=thickness; fixed contrast).
    contrast = np.full(lon2d.size, SED_DENSITY - C.RHO_CRUST)  # ~ -350
    t, d = mu.layer_to_tesseroids(np.zeros(lon2d.size), sed_km.ravel() * 1000.0,
                                  lon2d, lat2d, contrast)
    sed_eff = mu.tesseroid_gravity_grid(t, d, lon2d, lat2d, height_m=run_real.HEIGHT)
    print(f"RF sediment effect: {sed_eff.min():.1f}..{sed_eff.max():.1f} mGal")
    sed_free = bouguer - sed_eff

    # Invert with and without the RF sediment correction (same hyperparameters).
    moho_no = invert(bouguer, lon2d, lat2d, drho, z_ref, mu_reg, forward, RtR, n_lat, n_lon)
    moho_rf = invert(sed_free, lon2d, lat2d, drho, z_ref, mu_reg, forward, RtR, n_lat, n_lon)

    diff = moho_rf - moho_no
    west = lon2d <= 118
    print(f"\nMoho change (RF-sed − baseline): mean {diff.mean():+.2f}, "
          f"max |Δ| {np.abs(diff).max():.2f} km; WEST mean {diff[west].mean():+.2f} km")

    seis = mu.load_seismic_moho()
    for name, m in [("baseline (no RF sed)", moho_no), ("with RF sediment", moho_rf)]:
        itp = RegularGridInterpolator((lat2d[:, 0], lon2d[0, :]), m,
                                      bounds_error=False, fill_value=np.nan)
        est = itp(np.column_stack([seis.latitude, seis.longitude]))
        ok = np.isfinite(est)
        dd = est[ok] - seis.depth_km.values[ok]
        # western seismic subset
        w = seis.longitude.values[ok] <= 118
        print(f"  {name:22s}: all N={ok.sum()} mean {dd.mean():+.2f} std {dd.std():.2f} | "
              f"WEST N={w.sum()} mean {dd[w].mean():+.2f} std {dd[w].std():.2f} km")


if __name__ == "__main__":
    main()
