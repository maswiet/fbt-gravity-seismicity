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
# Fixed layer thicknesses (km); last is the half-space (0).
THICK = [0.5, 0.5, 1.0, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 0.0]
N_ITER = 10
LAM = 0.03                    # damping
MU = 0.6                     # smoothing (2nd-difference)
VS_MIN, VS_MAX = 0.6, 4.8
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
    vs = np.linspace(1.3, 4.3, n)                    # starting model
    L = np.zeros((n-2, n))                            # 2nd-difference smoothing
    for i in range(n-2):
        L[i, i:i+3] = [1, -2, 1]
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
        A = G.T @ G + (LAM**2)*np.eye(n) + (MU**2)*(L.T @ L)
        dvs = np.linalg.solve(A, G.T @ r)
        dvs = np.clip(dvs, -0.4, 0.4)
        vs = np.clip(vs + dvs, VS_MIN, VS_MAX)
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
    a1.invert_yaxis(); a1.set_ylim(35, 0)
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
    ax.invert_yaxis(); ax.set_ylim(35, 0)
    ax.set_xlabel("Vs (km/s)"); ax.set_ylabel("Depth (km)")
    ax.set_title("RF Vs inversion — flagship stations (Central Java)")
    ax.legend(); ax.grid(alpha=.3); fig.tight_layout()
    fig.savefig(C.FIGURES / "vs_profiles.png", dpi=200)
    print("Wrote", C.FIGURES / "vs_profiles.png")


if __name__ == "__main__":
    main()
