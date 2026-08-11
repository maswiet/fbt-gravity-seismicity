"""baseline_skill — honest predictive-skill benchmark at the 105 RF stations,
comparing the gravity model against trivial and recalibrated baselines
(reviewer's central request). Reports RMSE, MAE, bias, correlation and
Nash--Sutcliffe efficiency (NSE) relative to the constant-mean predictor.

NSE > 0  : beats predicting the mean depth everywhere.
NSE < 0  : WORSE than the constant-mean predictor.

Run (fbt env):  python moho_indonesia/baseline_skill.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402


def interp(da):
    return RegularGridInterpolator((da.latitude.values, da.longitude.values), da.values,
                                   bounds_error=False, fill_value=np.nan)


def main():
    seis = mu.load_seismic_moho()
    slon, slat, sd = seis.longitude.values, seis.latitude.values, seis.depth_km.values

    ours = interp(xr.open_dataarray(C.GRID_MOHO))(np.column_stack([slat, slon]))
    bnds = np.loadtxt(C.CRUST1_DIR / "crust1.bnds").reshape(180, 360, -1)
    crust = RegularGridInterpolator((np.arange(89.5, -90, -1.0)[::-1], np.arange(-179.5, 180, 1.0)),
                                    (-bnds[:, :, 8])[::-1, :], bounds_error=False,
                                    fill_value=np.nan)(np.column_stack([slat, slon]))
    gem = interp(xr.open_dataarray(C.DATA_EXTERNAL / "gemma" / "gemma_moho.nc"))(
        np.column_stack([slat, slon]))

    ok = np.isfinite(ours) & np.isfinite(crust) & np.isfinite(gem)
    s = sd[ok]
    rmse_mean = np.sqrt(np.mean((s - s.mean()) ** 2))          # constant-mean baseline

    # regional means (Sumatra <107, Java 107-115, East >115)
    reg = np.where(slon < 107, 0, np.where(slon < 115, 1, 2))[ok]
    regpred = np.array([s[reg == reg[i]].mean() for i in range(len(s))])
    # affine-recalibrated GEMMA / CRUST1.0 (a + b*model, least squares on these points)
    def affine(x):
        b, a = np.polyfit(x, s, 1)
        return a + b * x

    preds = {
        "Constant mean (30.4 km)": np.full_like(s, s.mean()),
        "Regional mean (3 zones)": regpred,
        "CRUST1.0": crust[ok],
        "CRUST1.0 (affine-recal.)": affine(crust[ok]),
        "GEMMA (raw)": gem[ok],
        "GEMMA (affine-recal.)": affine(gem[ok]),
        "This study (gravity)": ours[ok],
    }
    print(f"105 RF depths: mean {s.mean():.2f}, std {s.std(ddof=1):.2f}, range {s.min():.0f}-{s.max():.0f} km  "
          f"(N used = {ok.sum()})\n")
    print(f"{'Predictor':28s} {'RMSE':>5s} {'MAE':>5s} {'bias':>6s} {'r':>6s} {'NSE':>7s}")
    rows = []
    for name, p in preds.items():
        rmse = np.sqrt(np.mean((p - s) ** 2)); mae = np.mean(np.abs(p - s))
        bias = np.mean(p - s)
        r = np.corrcoef(p, s)[0, 1] if np.std(p) > 1e-9 else float("nan")
        nse = 1 - (rmse / rmse_mean) ** 2
        print(f"{name:28s} {rmse:5.2f} {mae:5.2f} {bias:+6.2f} {r:6.2f} {nse:+7.3f}")
        rows.append((name, rmse, mae, bias, r, nse))
    (C.FIGURES / "baseline_skill.txt").write_text(
        "predictor,rmse,mae,bias,r,nse\n" +
        "\n".join(f"{n},{rm:.2f},{ma:.2f},{bi:+.2f},{r:.2f},{ns:+.3f}" for n, rm, ma, bi, r, ns in rows) + "\n")
    print(f"\nWrote {C.FIGURES / 'baseline_skill.txt'}")


if __name__ == "__main__":
    main()
