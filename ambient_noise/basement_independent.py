"""
Depth-to-basement PURELY from the Romero & Schimmel ambient-noise autocorrelation
— independent of the receiver-function result.

Rationale (RF-free): a sedimentary section is reflective; the crystalline basement
below is comparatively transparent. So the basement two-way time is the DEEPEST
laterally-coherent, time-stable reflector before the autocorrelation reflectivity
dies out. We detect it from the total PCC+PWS stack:
  * envelope E(t) = |analytic(stack)| smoothed, weighted by the day-to-day phase
    coherence c(t) (only time-stable energy counts);
  * exclude the zero-lag region (t < TMIN);
  * basement TWT = the deepest coherent peak whose E exceeds a fraction of the
    in-band maximum (reflectivity-termination), taking the strongest-negative
    coherent peak nearby to refine the pick (R&S: basement = strong negative).
Depth = TWT * Vp/2 with an INDEPENDENT sediment Vp (literature), reported with a
Vp range as the uncertainty. RF is shown only as an external cross-check.

Run (fbt):  python ambient_noise/basement_independent.py
"""
from __future__ import annotations
import sys, glob, os, pathlib
import numpy as np, pandas as pd
from scipy.signal import hilbert
from scipy.ndimage import uniform_filter1d

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / "ambient_noise" / "cache"
FIG = ROOT / "figures" / "ambient_noise"; FIG.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "data" / "processed" / "rf_java"
TAG = "b1-6_w1_d5"
FS_EFF = 20.0
FLAG = ["BI4", "AF1", "AI4", "BG2"]
TMIN = 0.6                # exclude zero-lag/near-lag (s)
TMAX = 6.0
VP = 3.0                  # independent sediment Vp (km/s), central
VP_LO, VP_HI = 2.5, 3.5   # Vp range -> depth uncertainty


def stack_and_coherence(code):
    files = sorted(glob.glob(str(CACHE / f"{code}_*_{TAG}.npy")))
    rows = []
    for f in files:
        arr = np.load(f)
        if arr.shape[0] >= 5:
            rows.append(arr.mean(0))
    M = np.array(rows)
    ph = np.exp(1j * np.angle(hilbert(M, axis=1)))
    coh = np.abs(ph.mean(0))                      # day-to-day coherence per lag
    lin = M.mean(0)
    stack = lin * coh ** 2                        # PWS
    lag = np.arange(M.shape[1]) / FS_EFF
    return lag, stack, coh, M.shape[0]


def pick_basement(lag, stack, coh):
    """Basement = strongest coherent NEGATIVE reflector (R&S criterion: negative
    polarity = positive impedance contrast, sediment over harder basement)."""
    band = (lag >= TMIN) & (lag <= TMAX)
    cw = stack * coh                                         # coherence-weighted stack
    cw_band = np.where(band, cw, np.inf)
    # local minima (troughs) of the coherence-weighted stack
    trough = (cw[1:-1] < cw[:-2]) & (cw[1:-1] < cw[2:])
    ti = np.where(trough)[0] + 1
    ti = ti[band[ti] & (cw[ti] < 0)]
    if len(ti) == 0:
        return None
    order = ti[np.argsort(cw[ti])]                          # most negative first
    cand = [(float(lag[i]), float(cw[i])) for i in order[:3]]
    t_base = float(lag[order[0]])
    env = uniform_filter1d(np.abs(hilbert(stack)), size=int(0.15 * FS_EFF))
    wn = (env * coh); wn = wn / (wn[band].max() + 1e-12)
    return dict(t_base=t_base, cand=cand, wn=wn)


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    s_rf = pd.read_csv(DATA / "sediment_rf.csv")
    rows = []
    stat = [c for c in FLAG]
    fig, axes = plt.subplots(1, len(stat), figsize=(3.4 * len(stat), 7), sharey=True)
    if len(stat) == 1:
        axes = [axes]
    for ax, code in zip(axes, stat):
        lag, stack, coh, nd = stack_and_coherence(code)
        pk = pick_basement(lag, stack, coh)
        m = (lag >= TMIN) & (lag <= TMAX)
        s = stack[m] / (np.max(np.abs(stack[m])) + 1e-12)
        ax.plot(s, lag[m], "k", lw=1.1)
        ax.fill_betweenx(lag[m], 0, s, where=(s > 0), color="#B22", lw=0)
        ax.fill_betweenx(lag[m], 0, s, where=(s < 0), color="#2255BB", lw=0)
        ax.plot(pk["wn"][m], lag[m], color="green", lw=1.0, alpha=.7)   # coherence-weighted env
        rf = s_rf[s_rf.code == code]
        h_rf = float(rf.h_sed_km.iloc[0]) if len(rf) and rf.h_sed_km.iloc[0] > 0 else None
        depth = pk["t_base"] * VP / 2
        d_lo, d_hi = pk["t_base"] * VP_LO / 2, pk["t_base"] * VP_HI / 2
        for tc, _ in pk["cand"][1:]:
            ax.plot(0, tc, ">", color="gray", ms=7)        # other candidates
        ax.axhline(pk["t_base"], color="k", ls="-", lw=1.8)
        ax.text(-0.95, pk["t_base"] - 0.12, f"AN basement\n{pk['t_base']:.2f}s\n{depth:.1f} km",
                fontsize=8.5, color="k", va="bottom", fontweight="bold")
        if h_rf:
            twt_rf = 2 * h_rf / VP
            ax.axhline(twt_rf, color="green", ls="--", lw=1.3)
            ax.text(0.15, twt_rf + 0.12, f"RF {h_rf:.1f} km", color="green", fontsize=8)
        ax.set_ylim(TMAX, TMIN); ax.set_xlim(-1.05, 1.05); ax.set_xticks([])
        ax.set_title(f"{code}\n({nd} days)", fontsize=10, fontweight="bold")
        rows.append((code, pk["t_base"], depth, d_lo, d_hi, h_rf))
        print(f"  {code} candidates (twt,neg-strength): " +
              ", ".join(f"{t:.2f}s" for t, _ in pk["cand"]))
    axes[0].set_ylabel("two-way time (s)")
    fig.suptitle("Central Java — depth-to-basement from ambient-noise autocorrelation ONLY\n"
                 f"(deepest coherent reflector; Vp={VP} km/s, range {VP_LO}–{VP_HI}; "
                 "green dashed = RF cross-check)", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(FIG / "basement_independent.png", dpi=200); plt.close(fig)
    print("Wrote basement_independent.png\n")
    print(f"{'stn':4s} {'AN twt':>7s} {'AN depth':>9s} {'range(Vp)':>14s} {'RF depth':>9s}")
    for c, tb, d, dlo, dhi, hrf in rows:
        print(f"{c:4s} {tb:6.2f}s {d:7.1f}km  {dlo:5.1f}-{dhi:4.1f}km  "
              f"{(f'{hrf:.1f}km' if hrf else 'n/a'):>9s}")
    pd.DataFrame(rows, columns=["code", "an_twt_s", "an_depth_km", "depth_lo", "depth_hi",
                                "rf_depth_km"]).to_csv(DATA / "basement_an_independent.csv", index=False)
    print("\nWrote", DATA / "basement_an_independent.csv")


if __name__ == "__main__":
    main()
