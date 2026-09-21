"""
Romero & Schimmel (2018)-style figure set adapted to the Central Java basin,
from the MERAMEX ambient-noise autocorrelations + our RF sediment control.

Generates the analogues of the paper's:
  Fig 3  daily PCC autocorrelation SECTION for a flagship station + total stack
  Fig 5  field AC vs SYNTHETIC AC (2-layer model from the RF sediment thickness,
         our "well" control) + velocity-depth panel  -> the resonance/thickness test
  Fig 7  daily autocorrelogram section as a polarity IMAGE + time variability
  Fig 8  Central Java basement-depth map (RF sediment control) + AN flagship sites
  Fig 9  W-E basement depth cross-section

Uses the per-day PCC caches written by run_pipeline.py (band 1-6 Hz, whitened).

Run (fbt):  python ambient_noise/rs_figures.py
"""
from __future__ import annotations
import sys, glob, os, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rf_gravity_java"))
from _coast import add_coast
CACHE = ROOT / "ambient_noise" / "cache"
FIG = ROOT / "figures" / "ambient_noise"; FIG.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "data" / "processed" / "rf_java"
TAG = "b1-6_w1_d5"
FS_EFF = 20.0
FLAG = ["BI4", "AF1", "AI4", "BG2"]
VP_SED = 3.0        # km/s (P) for the sedimentary fill
VP_BASE = 5.8       # km/s basement


def daily_traces(code):
    """Per-day PWS trace matrix (ndays x nlag) + total stack, from the caches."""
    from scipy.signal import hilbert
    files = sorted(glob.glob(str(CACHE / f"{code}_*_{TAG}.npy")))
    days, rows = [], []
    for f in files:
        arr = np.load(f)
        if arr.shape[0] < 5:
            continue
        lin = arr.mean(0)
        coh = np.abs(np.exp(1j * np.angle(hilbert(arr, axis=1))).mean(0))
        rows.append(lin * coh ** 2)
        days.append(os.path.basename(f).split("_")[1])
    M = np.array(rows)
    tot_lin = M.mean(0)
    tot_coh = np.abs(np.exp(1j * np.angle(hilbert(M, axis=1))).mean(0))
    total = tot_lin * tot_coh ** 2
    lag = np.arange(M.shape[1]) / FS_EFF
    return days, M, total, lag


def rf_sed(code):
    s = pd.read_csv(DATA / "sediment_rf.csv")
    r = s[s.code == code]
    if len(r) and r.h_sed_km.iloc[0] > 0:
        return float(r.h_sed_km.iloc[0])
    return None


def ricker(t, f):
    a = (np.pi * f * t) ** 2
    return (1 - 2 * a) * np.exp(-a)


def synth_ac(H, lag, fpeak=2.5):
    """Synthetic zero-offset AC of a 2-layer model: sediment (Vp_SED) over basement.
    Negative polarity at the basement (positive impedance contrast)."""
    twt = 2 * H / VP_SED
    w = ricker(lag - lag.mean(), fpeak)
    tr = np.zeros_like(lag)
    # basement reflection (negative) + a weak first multiple
    for tt, amp in [(twt, -1.0), (2 * twt, 0.35)]:
        k = int(round(tt * FS_EFF))
        if 0 < k < len(tr):
            tr[k] += amp
    tr = np.convolve(tr, w, mode="same")
    return tr / (np.max(np.abs(tr)) + 1e-9), twt


# ---- Fig 3 : daily section + stack (one station) -------------------------
def fig3(code="BI4"):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    days, M, total, lag = daily_traces(code)
    H = rf_sed(code); twt = 2 * H / VP_SED if H else None
    LAG0 = 1.0                                    # start at 1 s (cf. R&S Fig 3)
    m = (lag >= LAG0) & (lag <= 6)
    fig, (ax, axs) = plt.subplots(1, 2, figsize=(11, 6.5), sharey=True,
                                  gridspec_kw=dict(width_ratios=[6, 1], wspace=0.03))
    x = np.arange(M.shape[0])
    norm = M[:, m] / (np.max(np.abs(M[:, m]), axis=1, keepdims=True) + 1e-9)
    for i in range(M.shape[0]):
        tr = norm[i] * 0.9 + x[i]
        ax.plot(tr, lag[m], color="k", lw=0.3)
        ax.fill_betweenx(lag[m], x[i], tr, where=(tr > x[i]), color="#B22", lw=0)
    ax.set_ylim(6, LAG0); ax.set_xlabel("day index"); ax.set_ylabel("two-way time (s)")
    ax.set_title(f"{code} — daily PCC autocorrelation section", fontweight="bold", fontsize=11)
    t2 = total[m] / (np.max(np.abs(total[m])) + 1e-9)
    axs.plot(t2, lag[m], "k", lw=1.2); axs.fill_betweenx(lag[m], 0, t2, where=(t2 > 0), color="#B22")
    axs.set_xlim(-1.1, 1.1); axs.set_title("stack", fontsize=10); axs.set_xticks([])
    if twt:
        for a in (ax, axs):
            a.axhline(twt, color="green", ls="--", lw=1.4)
        axs.text(1.15, twt, f"RF basement\n{twt:.1f}s (H={H}km)", color="green",
                 fontsize=8, va="center")
    fig.suptitle("Central Java MERAMEX — daily autocorrelation section (cf. R&S Fig 3)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96]); fig.savefig(FIG / "rs_fig3_section.png", dpi=200)
    plt.close(fig); print("Wrote rs_fig3_section.png")


# ---- Fig 5 : field vs synthetic AC + velocity model ----------------------
def fig5():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    stat = [c for c in FLAG if rf_sed(c)]
    n = len(stat)
    fig, axes = plt.subplots(n, 3, figsize=(12, 2.5 * n),
                             gridspec_kw=dict(width_ratios=[1.3, 1.3, 1.0], wspace=0.25, hspace=0.4))
    if n == 1:
        axes = axes[None, :]
    picks = []
    for r, code in enumerate(stat):
        _, _, total, lag = daily_traces(code)
        H = rf_sed(code)
        m = lag <= 6
        fld = total[m] / (np.max(np.abs(total[m])) + 1e-9)
        syn, twt = synth_ac(H, lag[m])
        a0, a1, a2 = axes[r]
        a0.plot(fld, lag[m], "k", lw=1.2); a0.fill_betweenx(lag[m], 0, fld, where=(fld > 0), color="#B22")
        a0.set_ylim(6, 0); a0.set_title(f"{code} — field AC", fontsize=10, fontweight="bold")
        a0.set_ylabel("TWT (s)"); a0.set_xlim(-1.1, 1.1); a0.set_xticks([])
        a1.plot(syn, lag[m], "b", lw=1.2); a1.fill_betweenx(lag[m], 0, syn, where=(syn > 0), color="#B22")
        a1.set_ylim(6, 0); a1.set_title("synthetic (2-layer, RF H)", fontsize=10, fontweight="bold")
        a1.set_xlim(-1.1, 1.1); a1.set_xticks([])
        a1.axhline(twt, color="green", ls="--", lw=1.3)
        a0.axhline(twt, color="green", ls="--", lw=1.3)
        # velocity model panel
        zt = np.array([0, H, H, 12]); vt = np.array([VP_SED, VP_SED, VP_BASE, VP_BASE])
        a2.plot(vt, zt, "C0", lw=2); a2.set_ylim(12, 0); a2.set_xlim(0, 7)
        a2.set_title("Vp model", fontsize=10, fontweight="bold"); a2.set_xlabel("Vp (km/s)")
        a2.set_ylabel("depth (km)"); a2.grid(alpha=.3)
        # field pick near predicted twt
        win = (lag[m] > twt - 0.7) & (lag[m] < twt + 0.7)
        if win.sum():
            seg = fld.copy(); seg[~win] = 0
            kpick = np.argmin(seg)               # strongest negative
            tpick = lag[m][kpick]
            hpick = tpick * VP_SED / 2
            picks.append((code, H, twt, tpick, hpick))
            a0.plot(fld[kpick], tpick, "gv", ms=8)
    fig.suptitle("Central Java — field vs synthetic autocorrelation & velocity model (cf. R&S Fig 5)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97]); fig.savefig(FIG / "rs_fig5_synthetic.png", dpi=200)
    plt.close(fig); print("Wrote rs_fig5_synthetic.png")
    if picks:
        print("  AN-resonance thickness vs RF:")
        for c, H, twt, tp, hp in picks:
            print(f"   {c}: RF H={H:.2f} km (twt {twt:.2f}s) | AN pick {tp:.2f}s -> H={hp:.2f} km")
    return picks


# ---- Fig 7 : daily section as image + variability ------------------------
def fig7(code="BI4"):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    days, M, total, lag = daily_traces(code)
    H = rf_sed(code); twt = 2 * H / VP_SED if H else None
    LAG0 = 1.0                                    # start at 1 s (cf. R&S Fig 3/7)
    m = (lag >= LAG0) & (lag <= 6)
    norm = M[:, m] / (np.max(np.abs(M[:, m]), axis=1, keepdims=True) + 1e-9)
    corr = np.array([np.corrcoef(M[i, m], total[m])[0, 1] for i in range(M.shape[0])])
    fig, (axt, axb) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True,
                                   gridspec_kw=dict(height_ratios=[1, 4], hspace=0.05))
    axt.plot(np.arange(len(corr)), corr, "k", lw=1); axt.set_ylabel("daily–stack corr")
    axt.set_ylim(0, 1.02); axt.grid(alpha=.3)
    axt.set_title(f"{code} — reflection-response time stability (cf. R&S Fig 7)", fontweight="bold", fontsize=11)
    im = axb.imshow(norm.T, aspect="auto", origin="upper", cmap="bwr", vmin=-1, vmax=1,
                    extent=[0, M.shape[0], lag[m][-1], lag[m][0]])
    axb.set_ylabel("two-way time (s)"); axb.set_xlabel("day index")
    if twt:
        axb.axhline(twt, color="green", ls="--", lw=1.4)
        axb.text(2, twt - 0.15, f"RF basement {twt:.1f}s", color="green", fontsize=9)
    fig.colorbar(im, ax=axb, fraction=0.03, pad=0.01, label="norm. amp (polarity)")
    fig.tight_layout(); fig.savefig(FIG / "rs_fig7_stability.png", dpi=200)
    plt.close(fig); print("Wrote rs_fig7_stability.png")


# ---- Fig 8 : basement map (RF control) + AN flagships --------------------
def fig8():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    s = pd.read_csv(DATA / "sediment_rf.csv")
    s = s[s.kind.isin(["EDL", "SAM"]) & (s.h_sed_km > 0)]
    REG = [109.4, 111.6, -8.2, -6.3]
    fig, ax = plt.subplots(figsize=(9, 7))
    sc = ax.scatter(s.lon, s.lat, c=s.h_sed_km, cmap="turbo", s=55, edgecolor="k", lw=.4,
                    vmax=np.percentile(s.h_sed_km, 95))
    fl = s[s.code.isin(FLAG)]
    ax.scatter(fl.lon, fl.lat, s=230, marker="*", facecolor="none", edgecolor="k", lw=1.6)
    for _, r in fl.iterrows():
        ax.text(r.lon + 0.03, r.lat + 0.02, r.code, fontsize=9, fontweight="bold")
    add_coast(ax, REG)
    ax.set_xlabel("Longitude (°E)"); ax.set_ylabel("Latitude (°)")
    ax.set_title("Central Java basement depth (RF sediment control)\n"
                 "stars = ambient-noise flagship stations  (cf. R&S Fig 8)",
                 fontweight="bold", fontsize=11)
    cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.02); cb.set_label("sediment thickness / basement depth (km)")
    fig.tight_layout(); fig.savefig(FIG / "rs_fig8_basement_map.png", dpi=200)
    plt.close(fig); print("Wrote rs_fig8_basement_map.png")


# ---- Fig 9 : W-E basement cross-section ----------------------------------
def fig9():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.interpolate import griddata
    s = pd.read_csv(DATA / "sediment_rf.csv")
    s = s[s.kind.isin(["EDL", "SAM"]) & (s.h_sed_km > 0)]
    lat0 = -7.5
    near = s[np.abs(s.lat - lat0) < 0.35].sort_values("lon")
    lon = np.linspace(109.5, 111.5, 100)
    prof = griddata(near.lon.values, near.h_sed_km.values, lon, method="linear")
    x = (lon - lon.mean()) * 111.32 * np.cos(np.deg2rad(lat0))
    fig, a = plt.subplots(figsize=(11, 4))
    a.fill_between(x, prof, 0, color="#C8DCE8"); a.plot(x, prof, "#065A82", lw=2, label="basement (RF)")
    xr = (near.lon.values - lon.mean()) * 111.32 * np.cos(np.deg2rad(lat0))
    a.scatter(xr, near.h_sed_km, c="#B0512F", s=45, zorder=5, edgecolor="white", label="RF stations")
    a.invert_yaxis(); a.set_xlabel("Distance W–E (km)"); a.set_ylabel("basement depth (km)")
    a.set_title(f"Central Java basement depth profile at {lat0}°S (cf. R&S Fig 9)", fontweight="bold")
    a.legend(); a.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(FIG / "rs_fig9_profile.png", dpi=200)
    plt.close(fig); print("Wrote rs_fig9_profile.png")


def main():
    fig3("BI4")
    fig5()
    fig7("BI4")
    fig8()
    fig9()


if __name__ == "__main__":
    main()
