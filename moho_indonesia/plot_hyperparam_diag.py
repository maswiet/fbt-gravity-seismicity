"""
plot_hyperparam_diag — U&B (2017) Fig. 10 style hyperparameter diagnostics,
marking the ADOPTED (physically reasonable) point rather than the raw argmin.

The seismic misfit decreases monotonically with Delta-rho (a Delta-rho vs z_ref /
Moho-amplitude trade-off), so the calibration argmin runs away to unphysically
high Delta-rho; we therefore adopt a physical Delta-rho (400 kg/m^3, cf. Uieda &
Barbosa 2017 ~400) confirmed by the independent AusMoho comparison.

Reads the sweep arrays from `hyperparameters_sweep.npz` if present; otherwise
reconstructs them from a calibrate.py --fine log (in run order) and saves the npz.

Run:  python moho_indonesia/plot_hyperparam_diag.py [calibrate_log]
"""
from __future__ import annotations

import pathlib
import re
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402

ADOPTED_ZREF, ADOPTED_DRHO = 35.0, 400.0        # physical crust-mantle contrast (cf. U&B 2017)
NPZ = C.DATA_PROCESSED / "hyperparameters_sweep.npz"


def _reconstruct_from_log(logpath):
    text = pathlib.Path(logpath).read_text().splitlines()
    mu_mse = [float(re.search(r"testMSE=\s*([\d.]+)", l).group(1))
              for l in text if "testMSE" in l]
    rms = [float(re.search(r"seisRMS=\s*([\d.]+)", l).group(1))
           for l in text if "seisRMS" in l]
    mu_set = C.MU_VALUES
    zref, drho = np.asarray(C.ZREF_VALUES), np.asarray(C.DRHO_VALUES)
    assert len(mu_mse) == len(mu_set), (len(mu_mse), len(mu_set))
    assert len(rms) == len(zref) * len(drho), (len(rms), len(zref) * len(drho))
    mse_surface = (np.array(rms) ** 2).reshape(len(zref), len(drho))  # (z_ref, drho)
    np.savez(NPZ, mu_set=mu_set, mu_mse=mu_mse, zref=zref, drho=drho,
             mse_surface=mse_surface)
    return mu_set, np.array(mu_mse), zref, drho, mse_surface


def main(logpath=None):
    if NPZ.exists() and logpath is None:
        z = np.load(NPZ)
        mu_set, mu_mse, zref, drho, mse_surface = (
            z["mu_set"], z["mu_mse"], z["zref"], z["drho"], z["mse_surface"])
    else:
        mu_set, mu_mse, zref, drho, mse_surface = _reconstruct_from_log(logpath)

    plt.rcParams.update({"font.size": 12, "axes.titlesize": 13})
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.6, 9.2))

    # (a) mu cross-validation
    ax1.loglog(mu_set, mu_mse, "-", color="#2f6db0", lw=2.2)
    ax1.loglog(mu_set, mu_mse, "o", color="#2f6db0", ms=4.5)
    imin = int(np.argmin(mu_mse))
    ax1.plot(mu_set[imin], mu_mse[imin], "^", color="#c0392b", ms=15, mec="k", zorder=6)
    ax1.set(xlabel="Regularization parameter", ylabel="Mean Square Error (mGal²)",
            title="(a) Cross-validation (μ)")
    ax1.grid(True, which="both", ls=":", color="0.8")
    ax1.set_axisbelow(True)

    # (b) (z_ref, drho) surface — mark the ADOPTED point (inside the frame)
    im = ax2.pcolormesh(zref, drho, mse_surface.T, shading="gouraud", cmap="magma")
    ax2.plot(ADOPTED_ZREF, ADOPTED_DRHO, "^", color="#c0392b", ms=15, mec="k",
             zorder=6, label="adopted (z_ref=35, Δρ=400)")
    ax2.set(xlabel="Reference level (km)", ylabel="Density contrast (kg m⁻³)",
            title="(b) Validation (Δρ, z_ref)")
    ax2.legend(loc="lower right", fontsize=9, framealpha=0.85)
    fig.colorbar(im, ax=ax2, label="Mean Square Error (km²)", pad=0.02)

    fig.tight_layout()
    out = C.FIGURES / "hyperparameters.png"
    fig.savefig(out, dpi=170)
    print("Wrote", out, "| adopted z_ref=35, drho=400 (argmin runs away to high drho)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
