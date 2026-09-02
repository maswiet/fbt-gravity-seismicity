"""
Tahap 3 — Sediment layer from receiver functions.

Robust estimator: on each station's stacked radial RF we pick the sediment
P-to-S conversion delay t_Ps (first strong positive peak after the direct P),
and invert it for sediment thickness with the standard Ps move-out relation

    t_Ps = H * ( sqrt(1/Vs^2 - p^2) - sqrt(1/Vp^2 - p^2) )

(assumed sediment Vs, Vp=2*Vs; p = ray parameter). This is far more noise-robust
than full-waveform fitting for short-period data. Each result is VALIDATED by
FORWARD MODELLING with the Herrmann CPS program hrftn96 (pemodelan maju RF):
the synthetic RF for the derived (H, Vs) layer is overlain on the observed RF.

Output:
  data/processed/rf_java/sediment_rf.csv
  data/processed/rf_java/vs_models/<STA>.mod   (best model96)
  figures/rf_java/fwd_demo_<STA>.png           (observed vs hrftn96 synthetic)
  figures/rf_java/sediment_rf_map.png

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
VS_SED = 1.5              # assumed sediment shear velocity (km/s) — young Java fill
VPVS_SED = 2.0
PS_WIN = (0.3, 2.5)      # sediment Ps search window (s) — 0.3-2.5s ~ 1-6 km at Vs 1.5
MIN_PS_AMP = 0.10        # min positive amplitude (rel. to P) to call it sediment

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


def thickness_from_tps(t_ps, rayp):
    """Invert Ps delay for sediment thickness (km) via the move-out relation."""
    vs, vp = VS_SED, VS_SED * VPVS_SED
    term = np.sqrt(max(1.0/vs**2 - rayp**2, 1e-6)) - \
        np.sqrt(max(1.0/vp**2 - rayp**2, 1e-6))
    return t_ps / term if term > 0 else 0.0


def pick_tps(data, b, dt):
    """Pick the sediment Ps delay: strongest positive peak in PS_WIN, rel. to P."""
    i0 = int(round((0.0 - b) / dt))
    p_amp = data[i0] if abs(data[i0]) > 1e-9 else 1.0
    ia = i0 + int(round(PS_WIN[0] / dt))
    ib = i0 + int(round(PS_WIN[1] / dt))
    seg = np.array(data[ia:ib], dtype=float) / p_amp
    if seg.size < 3:
        return 0.0, 0.0
    # First local maximum exceeding the threshold = the sediment Ps conversion
    # (the shallowest interface converts earliest). Fall back to global peak.
    for k in range(1, len(seg) - 1):
        if seg[k] > MIN_PS_AMP and seg[k] >= seg[k-1] and seg[k] > seg[k+1]:
            return PS_WIN[0] + k * dt, float(seg[k])
    k = int(np.argmax(seg))
    return (PS_WIN[0] + k*dt, float(seg[k])) if seg[k] >= MIN_PS_AMP else (0.0, float(seg[k]))


def main():
    import obspy
    import pandas as pd
    C.ensure_dirs()
    summ = pd.read_csv(C.DATA_PROCESSED / "rf_summary.csv")
    work = tempfile.mkdtemp(prefix="hrftn_")

    rows = []
    for _, s in summ.iterrows():
        code = s["code"]
        sac = C.RF_DIR / f"{code}_rf.sac"
        if not sac.exists():
            continue
        tr = obspy.read(str(sac))[0]
        rayp = float(getattr(tr.stats.sac, "user4", s["mean_rayp_skm"]))
        t_ps, amp = pick_tps(tr.data, float(tr.stats.sac.b), tr.stats.delta)
        h = thickness_from_tps(t_ps, rayp) if t_ps > 0 else 0.0
        write_model96(C.VS_DIR / f"{code}.mod", sed_layers(h))
        rows.append(dict(code=code, lat=s["lat"], lon=s["lon"], kind=s["kind"],
                         n_rf=int(s["n_rf"]), t_ps_s=round(t_ps, 2),
                         ps_amp=round(amp, 3), vs_sed=VS_SED,
                         h_sed_km=round(h, 2)))
        if code == "BGB":
            _fwd_demo(code, tr, h, rayp, work)

    df = pd.DataFrame(rows)
    df.to_csv(C.SEDIMENT_CSV, index=False)
    land = df[df.kind.isin(["EDL", "SAM"])]
    res = land[land.h_sed_km > 0]
    print(f"Sediment from RF: {len(df)} stations, {len(res)} with resolvable Ps.")
    print(f"  H_sed (resolved): mean {res.h_sed_km.mean():.2f} km, median "
          f"{res.h_sed_km.median():.2f} km, range {res.h_sed_km.min():.2f}"
          f"-{res.h_sed_km.max():.2f} km")
    _sed_map(df)
    print("Wrote", C.SEDIMENT_CSV)


def _fwd_demo(code, tr, h, rayp, work):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    dt = tr.stats.delta; b = float(tr.stats.sac.b)
    i0 = int(round((0.0 - b) / dt))          # observed direct-P at t=0 (aligned)
    obs = np.array(tr.data, float) / (tr.data[i0] or 1.0)
    tobs = (np.arange(len(obs)) - i0) * dt
    syn, sdt, _ = hrftn96_rf(sed_layers(h), rayp, work)
    jP = int(np.argmax(syn))                  # hrftn96 direct-P = global max
    syn = syn / (syn[jP] or 1.0)
    tsyn = (np.arange(len(syn)) - jP) * sdt
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(tobs, obs, "k", lw=1.6, label=f"Observed RF ({code})")
    ax.plot(tsyn, syn, "r", lw=1.5, ls="--",
            label=f"hrftn96 synthetic (H={h:.1f} km, Vs={VS_SED} km/s)")
    ax.axvline(0, color="gray", lw=.6)
    ax.set_xlim(-2, 12); ax.set_xlabel("Time after P (s)")
    ax.set_ylabel("RF amplitude (norm.)")
    ax.set_title(f"Forward modelling of RF (Herrmann hrftn96) — {code}")
    ax.legend(); ax.grid(alpha=.3)
    out = C.FIGURES / f"fwd_demo_{code}.png"
    fig.tight_layout(); fig.savefig(out, dpi=200); print("Wrote", out)


def _sed_map(df):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    land = df[df.kind.isin(["EDL", "SAM"])]
    fig, ax = plt.subplots(figsize=(9, 6))
    vmax = max(2.0, float(land.h_sed_km.quantile(.95)))
    sc = ax.scatter(land.lon, land.lat, c=land.h_sed_km, s=70, cmap="turbo",
                    edgecolor="k", vmin=0, vmax=vmax)
    plt.colorbar(sc, label="RF sediment thickness (km)")
    ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
    ax.set_title("MERAMEX RF-derived sediment thickness — Central Java")
    ax.set_aspect(1.0)
    out = C.FIGURES / "sediment_rf_map.png"
    fig.tight_layout(); fig.savefig(out, dpi=200); print("Wrote", out)


if __name__ == "__main__":
    main()
