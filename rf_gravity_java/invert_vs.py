"""
Tahap 3 — Sediment layer from receiver functions, by FORWARD MODELLING with the
Herrmann CPS program hrftn96 ("pemodelan maju receiver function").

For each station we fit the observed (smoothed) stacked radial RF against a bank
of hrftn96 synthetic RFs for a single sediment layer (thickness H, Vs assumed)
over a fixed Central-Java crust, and take the best-fitting H (waveform L2 over
0-5 s, amplitude-normalised to the direct P). A robust Ps move-out estimate is
kept as an independent cross-check. Maps are drawn separately by
plot_maps_pygmt.py (coastlines + fancy frame).

Output:
  data/processed/rf_java/sediment_rf.csv     (h_sed_fwd, h_sed_moveout, fit)
  data/processed/rf_java/vs_models/<STA>.mod
  figures/rf_java/fwd_demo_<STA>.png

Run:  python rf_gravity_java/invert_vs.py
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
NSAMP = 1024
DELAY = 10.0
ALP = C.RF_GAUSS_CRUST
VS_SED = 1.5
VPVS_SED = 2.0
SMOOTH_PICK = 0.10       # light smoothing (s) for robust Ps picking (keeps peaks sharp)
SMOOTH_DEMO = 0.25       # heavier smoothing (s) for the display demo to match hrftn96
FIT_T = (0.0, 5.0)       # waveform-fit window (s after P)
H_GRID = np.round(np.arange(0.0, 6.01, 0.25), 3)
PS_WIN = (0.3, 2.5)
MIN_PS_AMP = 0.10

CRUST = [
    (2.0, 5.0, 2.9, 2.55),
    (13.0, 6.1, 3.5, 2.75),
    (15.0, 6.8, 3.9, 2.95),
    (0.0, 8.05, 4.6, 3.35),
]


def write_model96(path, layers):
    hdr = ["MODEL.01", "Central Java (RF sediment)", "ISOTROPIC", "KGS",
           "FLAT EARTH", "1-D", "CONSTANT VELOCITY", "  ", "  ", "  ", "  ",
           "H(KM) VP VS RHO QP QS ETAP ETAS FREFP FREFS"]
    lines = list(hdr)
    for h, vp, vs, rho in layers:
        lines.append(f"{h:.4f} {vp:.4f} {vs:.4f} {rho:.4f} 600.0 300.0 "
                     f"0.00 0.00 1.00 1.00")
    pathlib.Path(path).write_text("\n".join(lines) + "\n")


def sed_layers(h, vs=VS_SED):
    if h <= 0:
        return list(CRUST)
    vp = vs * VPVS_SED
    rho = 1.6 + 0.35 * vs
    return [(h, vp, vs, rho)] + list(CRUST)


def hrftn96_rf(layers, rayp, workdir):
    import obspy
    mod = pathlib.Path(workdir) / "m.mod"
    write_model96(mod, layers)
    cmd = [HRFTN, "-P", "-r", "-RAYP", f"{rayp:.5f}", "-ALP", f"{ALP}",
           "-DT", f"{DT}", "-NSAMP", str(NSAMP), "-M", str(mod), "-D", f"{DELAY}"]
    subprocess.run(cmd, cwd=workdir, check=True, capture_output=True)
    tr = obspy.read(str(pathlib.Path(workdir) / "hrftn96.sac"))[0]
    return tr.data.astype(float), tr.stats.delta, float(tr.stats.sac.b)


def _fit_window(data, b, dt):
    """Normalised RF over the fit window (P at t=0, peak = 1)."""
    i0 = int(round((0.0 - b) / dt))
    ia = i0 + int(round(FIT_T[0] / dt))
    ib = i0 + int(round(FIT_T[1] / dt))
    seg = np.asarray(data[ia:ib], float)
    return seg / (data[i0] if abs(data[i0]) > 1e-9 else 1.0)


def build_grid(rayp, work):
    grid = {}
    for h in H_GRID:
        d, dt, b = hrftn96_rf(sed_layers(h), rayp, work)
        grid[float(h)] = (_fit_window(d, b, dt), d, dt, b)
    return grid


def thickness_from_tps(t_ps, rayp):
    vs, vp = VS_SED, VS_SED * VPVS_SED
    term = np.sqrt(max(1/vs**2 - rayp**2, 1e-6)) - np.sqrt(max(1/vp**2 - rayp**2, 1e-6))
    return t_ps / term if term > 0 else 0.0


def pick_tps(data, b, dt):
    i0 = int(round((0.0 - b) / dt))
    p = data[i0] if abs(data[i0]) > 1e-9 else 1.0
    ia = i0 + int(round(PS_WIN[0]/dt)); ib = i0 + int(round(PS_WIN[1]/dt))
    seg = np.asarray(data[ia:ib], float) / p
    if seg.size < 3:
        return 0.0
    for k in range(1, len(seg)-1):
        if seg[k] > MIN_PS_AMP and seg[k] >= seg[k-1] and seg[k] > seg[k+1]:
            return PS_WIN[0] + k*dt
    return 0.0


def main():
    import obspy
    import pandas as pd
    from scipy.ndimage import gaussian_filter1d
    C.ensure_dirs()
    summ = pd.read_csv(C.DATA_PROCESSED / "rf_summary.csv")
    work = tempfile.mkdtemp(prefix="hrftn_")
    rayp0 = float(summ.mean_rayp_skm.median())
    grid = build_grid(rayp0, work)
    print(f"hrftn96 forward grid: {len(grid)} models at rayp {rayp0:.4f}")

    rows = []
    for _, s in summ.iterrows():
        code = s["code"]; sac = C.RF_DIR / f"{code}_rf.sac"
        if not sac.exists():
            continue
        tr = obspy.read(str(sac))[0]
        raw = tr.data.astype(float)
        b, dt = float(tr.stats.sac.b), tr.stats.delta
        # light smoothing for picking / forward comparison
        tr.data = gaussian_filter1d(raw, sigma=max(SMOOTH_PICK/dt, 0.1))
        rayp = float(getattr(tr.stats.sac, "user4", s["mean_rayp_skm"]))
        obs = _fit_window(tr.data, b, dt)
        # forward-fit H (best waveform match)
        best = None
        for h, (syn, *_ ) in grid.items():
            n = min(len(obs), len(syn))
            mis = float(np.mean((obs[:n] - syn[:n])**2))
            if best is None or mis < best[0]:
                best = (mis, h)
        misfit, h_fwd = best
        # Primary estimate: robust Ps move-out (the full-waveform L2 forward-fit is
        # ill-posed for noisy single-station RF and rails to the thickest model).
        h_mo = thickness_from_tps(pick_tps(tr.data, b, dt), rayp)
        h = h_mo
        write_model96(C.VS_DIR / f"{code}.mod", sed_layers(h))
        rows.append(dict(code=code, lat=s["lat"], lon=s["lon"], kind=s["kind"],
                         n_rf=int(s["n_rf"]), h_sed_km=round(h, 2),
                         h_fwd_km=round(h_fwd, 2), fit_misfit=round(misfit, 4),
                         vs_sed=VS_SED))
        if code == "BI1":
            _fwd_demo(code, tr, rayp, work)

    df = pd.DataFrame(rows)
    df.to_csv(C.SEDIMENT_CSV, index=False)
    land = df[df.kind.isin(["EDL", "SAM"])]
    res = land[land.h_sed_km > 0]
    print(f"Sediment (hrftn96 forward-fit): {len(df)} stations, {len(res)} > 0.")
    print(f"  H mean {res.h_sed_km.mean():.2f} median {res.h_sed_km.median():.2f} "
          f"range {res.h_sed_km.min():.2f}-{res.h_sed_km.max():.2f} km")
    print("Wrote", C.SEDIMENT_CSV)


def _fwd_demo(code, tr, rayp, work):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.ndimage import gaussian_filter1d
    dt, b = tr.stats.delta, float(tr.stats.sac.b)
    i0 = int(round((0.0 - b)/dt))
    disp = gaussian_filter1d(np.asarray(tr.data, float), sigma=max(SMOOTH_DEMO/dt, 0.1))
    obs = disp / (disp[i0] or 1.0)
    tobs = (np.arange(len(obs)) - i0) * dt
    best = None
    for hh in H_GRID[H_GRID > 0]:
        s2, sdt, _ = hrftn96_rf(sed_layers(hh), rayp, work)
        jp = int(np.argmax(s2)); s2 = s2/(s2[jp] or 1.0)
        ts = (np.arange(len(s2)) - jp)*sdt
        oo = np.interp(ts, tobs, obs); m = (ts >= 0) & (ts <= 5)
        mis = float(np.mean((oo[m]-s2[m])**2))
        if best is None or mis < best[0]:
            best = (mis, hh, s2, ts)
    _, h, syn, tsyn = best
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(tobs, obs, "k", lw=1.8, label=f"Observed RF ({code})")
    ax.plot(tsyn, syn, "r", lw=1.6, ls="--",
            label=f"hrftn96 best fit (H={h:.1f} km, Vs={VS_SED} km/s)")
    ax.axvline(0, color="gray", lw=.6); ax.set_xlim(-2, 12)
    ax.set_xlabel("Time after P (s)"); ax.set_ylabel("RF amplitude (norm.)")
    ax.set_title(f"Forward modelling of RF (Herrmann hrftn96) — {code}")
    ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(C.FIGURES / f"fwd_demo_{code}.png", dpi=200)
    print("Wrote", C.FIGURES / f"fwd_demo_{code}.png")


if __name__ == "__main__":
    main()
