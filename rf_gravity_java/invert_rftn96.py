"""
Tahap 3b — Full layered shear-velocity inversion of receiver functions for a few
flagship stations (the deeper "inversion" slide).

Method: linearised, damped, smoothed least-squares inversion of the radial RF for
the Vs of a stack of fixed-thickness layers — the same scheme as Herrmann CPS
`rftn96` — with the CPS `hrftn96` Haskell-matrix forward operator and a
finite-difference Jacobian. Vp and density are tied to Vs (Vp/Vs, Brocher 2005).

Output:
  data/processed/rf_java/vs_profiles.csv
  figures/rf_java/vs_inversion_<STA>.png   (Vs(z) + RF fit per station)
  figures/rf_java/vs_profiles.png          (all flagship profiles)

Run:  python rf_gravity_java/invert_rftn96.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C

HRFTN = str(C.CPS_BIN / "hrftn96")
DT = 0.05
NSAMP = 2048
DELAY = 10.0
ALP = C.RF_GAUSS_CRUST
FIT_T = (-1.0, 12.0)          # RF fit window (s)
SMOOTH_S = 0.25
# Fixed layer thicknesses (km); last is the half-space (0). Extended to upper mantle.
THICK = [0.5, 0.5, 1.0, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 0.0]
# AK135/PREM-like continental reference & starting model (Vs increases with depth).
REF_VS = np.array([1.4, 1.9, 2.5, 2.9, 3.1, 3.3, 3.45, 3.55, 3.65, 3.75, 3.9,
                   4.3, 4.45, 4.5])
DEPTH_TOP = np.array([0, 0.5, 1, 2, 3, 4.5, 6.5, 9, 12, 16, 21, 27, 35, 45.0])
N_ITER = 12
LAM = 0.05                    # prior damping toward REF_VS (light — let data shape crust)
MU = 0.4                      # smoothing (2nd-difference)
VS_MIN, VS_MAX = 0.6, 4.8
VS_CRUST_MAX = 4.0            # crustal layers (<28 km) capped below mantle speed
MANTLE_Z = 28.0              # depth (km) above which layers stay crustal
N_MONO = 3                    # top 3 layers (sediment) free; below forced increasing
N_FLAGSHIP = 4


def brocher_rho(vp):           # vp,rho in km/s, g/cc (Brocher 2005)
    return (1.6612*vp - 0.4721*vp**2 + 0.0671*vp**3 - 0.0043*vp**4 + 0.000106*vp**5)


def vs_to_layers(vs):
    layers = []
    for i, (h, v) in enumerate(zip(THICK, vs)):
        vpvs = 2.0 if i < 2 else (1.75 if v < 3.6 else 1.78)
        vp = v * vpvs
        layers.append((h, vp, v, max(brocher_rho(vp), 2.0)))
    return layers


def write_model96(path, layers):
    hdr = ["MODEL.01", "Vs inversion", "ISOTROPIC", "KGS", "FLAT EARTH", "1-D",
           "CONSTANT VELOCITY", " ", " ", " ", " ",
           "H(KM) VP VS RHO QP QS ETAP ETAS FREFP FREFS"]
    L = list(hdr)
    for h, vp, vs, rho in layers:
        L.append(f"{h:.4f} {vp:.4f} {vs:.4f} {rho:.4f} 600.0 300.0 0 0 1 1")
    pathlib.Path(path).write_text("\n".join(L) + "\n")


def forward(vs, rayp, work, tref):
    """RF predicted by hrftn96 for model vs, resampled to time axis tref (P=0, norm)."""
    import obspy
    mod = pathlib.Path(work) / "m.mod"
    write_model96(mod, vs_to_layers(vs))
    subprocess.run([HRFTN, "-P", "-r", "-RAYP", f"{rayp:.5f}", "-ALP", f"{ALP}",
                    "-DT", f"{DT}", "-NSAMP", str(NSAMP), "-M", str(mod),
                    "-D", f"{DELAY}"], cwd=work, check=True, capture_output=True)
    tr = obspy.read(str(pathlib.Path(work) / "hrftn96.sac"))[0]
    d = tr.data.astype(float); jp = int(np.argmax(d)); d = d / (d[jp] or 1.0)
    t = (np.arange(len(d)) - jp) * tr.stats.delta
    return np.interp(tref, t, d, left=0, right=0)


def invert_station(code, rayp, work):
    import obspy
    from scipy.ndimage import gaussian_filter1d
    tr = obspy.read(str(C.RF_DIR / f"{code}_rf.sac"))[0]
    dt, b = tr.stats.delta, float(tr.stats.sac.b)
    d = gaussian_filter1d(tr.data.astype(float), sigma=max(SMOOTH_S/dt, 0.1))
    i0 = int(round((0.0 - b)/dt)); d = d / (d[i0] or 1.0)
    tobs = (np.arange(len(d)) - i0) * dt
    tref = np.arange(FIT_T[0], FIT_T[1] + dt/2, dt)
    obs = np.interp(tref, tobs, d, left=0, right=0)

    n = len(THICK)
    ref = REF_VS.copy()
    vs = ref.copy()                                   # start from the PREM-like model
    L = np.zeros((n-2, n))                            # 2nd-difference smoothing
    for i in range(n-2):
        L[i, i:i+3] = [1, -2, 1]
    I = np.eye(n)
    hist = []
    for it in range(N_ITER):
        pred = forward(vs, rayp, work, tref)
        r = obs - pred
        rms = float(np.sqrt(np.mean(r**2))); hist.append(rms)
        G = np.zeros((len(tref), n))
        for j in range(n):
            dv = 0.05
            vj = vs.copy(); vj[j] = np.clip(vj[j] + dv, VS_MIN, VS_MAX)
            G[:, j] = (forward(vj, rayp, work, tref) - pred) / dv
        # damped, smoothed, prior-constrained Gauss-Newton step
        A = G.T @ G + (LAM**2)*I + (MU**2)*(L.T @ L)
        rhs = G.T @ r - (LAM**2)*(vs - ref) - (MU**2)*(L.T @ (L @ vs))
        dvs = np.clip(np.linalg.solve(A, rhs), -0.4, 0.4)
        vs = np.clip(vs + dvs, VS_MIN, VS_MAX)
        # keep crustal layers crustal (<VS_CRUST_MAX above the mantle depth)
        for i in range(n):
            if DEPTH_TOP[i] < MANTLE_Z:
                vs[i] = min(vs[i], VS_CRUST_MAX)
        # enforce velocity increasing with depth below the sediment (PREM-like)
        for i in range(max(N_MONO, 1), n):
            vs[i] = max(vs[i], vs[i-1])
        vs[-1] = REF_VS[-1]                            # fix mantle half-space
    pred = forward(vs, rayp, work, tref)
    rms = float(np.sqrt(np.mean((obs-pred)**2))); hist.append(rms)
    depth = np.concatenate([[0], np.cumsum([t for t in THICK[:-1]])])
    return dict(code=code, vs=vs, depth_top=depth, tref=tref, obs=obs,
                pred=pred, rms=rms, hist=hist)


def plot_station(res):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 5.2),
                                 gridspec_kw=dict(width_ratios=[1, 1.5]))
    # Vs profile (step)
    z = list(res["depth_top"]) + [res["depth_top"][-1] + 6]
    v = list(res["vs"]) + [res["vs"][-1]]
    a1.step(v, z, where="post", color="C0", lw=2)
    a1.invert_yaxis(); a1.set_ylim(52, 0)
    a1.set_xlabel("Vs (km/s)"); a1.set_ylabel("Depth (km)")
    a1.set_title(f"Vs model — {res['code']}"); a1.grid(alpha=.3)
    # RF fit
    a2.plot(res["tref"], res["obs"], "k", lw=1.8, label="Observed RF")
    a2.plot(res["tref"], res["pred"], "r--", lw=1.6,
            label=f"Predicted (RMS {res['rms']:.3f})")
    a2.set_xlim(-1, 12); a2.axvline(0, color="gray", lw=.6)
    a2.set_xlabel("Time after P (s)"); a2.set_ylabel("RF amp (norm.)")
    a2.set_title("RF fit"); a2.legend(); a2.grid(alpha=.3)
    fig.tight_layout()
    out = C.FIGURES / f"vs_inversion_{res['code']}.png"
    fig.savefig(out, dpi=200); plt.close(fig)
    print("Wrote", out)


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    C.ensure_dirs()
    sed = pd.read_csv(C.SEDIMENT_CSV)
    land = sed[sed.kind.isin(["EDL", "SAM"])].copy()
    cand = land[land.n_rf >= 6].sort_values(["fit_misfit", "n_rf"],
                                            ascending=[True, False])
    picks = cand.head(N_FLAGSHIP)["code"].tolist()
    summ = pd.read_csv(C.DATA_PROCESSED / "rf_summary.csv").set_index("code")
    print("Flagship stations:", picks)
    work = tempfile.mkdtemp(prefix="rftn_")

    results, rows = [], []
    for code in picks:
        rayp = float(summ.loc[code, "mean_rayp_skm"])
        res = invert_station(code, rayp, work)
        plot_station(res); results.append(res)
        for zt, v in zip(res["depth_top"], res["vs"]):
            rows.append(dict(code=code, depth_km=round(float(zt), 2), vs=round(float(v), 3)))
        print(f"  {code}: final RMS {res['rms']:.3f} ({res['hist'][0]:.3f} -> {res['rms']:.3f})")
    pd.DataFrame(rows).to_csv(C.DATA_PROCESSED / "vs_profiles.csv", index=False)

    # combined profiles
    fig, ax = plt.subplots(figsize=(5.5, 6.5))
    for res in results:
        z = list(res["depth_top"]) + [res["depth_top"][-1] + 6]
        v = list(res["vs"]) + [res["vs"][-1]]
        ax.step(v, z, where="post", lw=2, label=res["code"])
    ax.invert_yaxis(); ax.set_ylim(52, 0)
    ax.set_xlabel("Vs (km/s)"); ax.set_ylabel("Depth (km)")
    ax.set_title("RF Vs inversion — flagship stations (Central Java)")
    ax.legend(); ax.grid(alpha=.3); fig.tight_layout()
    fig.savefig(C.FIGURES / "vs_profiles.png", dpi=200)
    print("Wrote", C.FIGURES / "vs_profiles.png")


if __name__ == "__main__":
    main()
