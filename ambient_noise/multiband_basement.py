"""
RF-INDEPENDENT depth-to-basement from ambient-noise autocorrelation, with
zero-lag SIDELOBE discrimination (Romero & Schimmel 2018, Fig 6 strategy).

A single-band autocorrelation is contaminated by zero-lag sidelobes that are
identical between stations (same source wavelet) and therefore mimic reflectors.
Real reflections stay at a FIXED two-way time across frequency bands, sidelobes
move. So we compute the PCC autocorrelation in several one-octave bands, keep only
the troughs that are STABLE across bands (a real reflection), and take the basement
as the strongest band-stable negative reflector. TWT -> depth uses an independent
sediment Vp (literature), with a Vp range as the uncertainty. RF is a cross-check.

Reads each flagship day ONCE (I/O bound) and autocorrelates it in every band.
Run (fbt):  python ambient_noise/multiband_basement.py --max-days 60
"""
from __future__ import annotations
import sys, os, glob, argparse, pathlib
import numpy as np
from scipy.signal import hilbert
from scipy.ndimage import uniform_filter1d

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ambient_noise"))
MER = pathlib.Path("/Volumes/Untitled/MERAMEX DATA")
INFO = MER / "DOY 260_1905" / "INFO.DAT"
INDEX = ROOT / "ambient_noise" / "pri0_index.txt"
CACHE = ROOT / "ambient_noise" / "cache_mb"; CACHE.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "figures" / "ambient_noise"; FIG.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "data" / "processed" / "rf_java"

FS, DECI = 100.0, 5
FS_EFF = FS / DECI
BANDS = [(1.0, 4.0), (2.0, 6.0), (3.0, 8.0)]
WIN, MAXLAG = 1800, 8.0
TMIN, TMAX = 0.6, 6.0
VP, VP_LO, VP_HI = 3.0, 2.5, 3.5
STATIONS = {"BI4": ["3080"], "AF1": ["3135"], "AI4": ["3043", "3092"], "BG2": ["3121"]}


def whiten(w, fs, band):
    w = w - w.mean()
    env = uniform_filter1d(np.abs(w), size=max(1, int(fs)))
    w = w / (env + 1e-9 * env.max())
    W = np.fft.rfft(w); f = np.fft.rfftfreq(len(w), 1.0 / fs)
    sm = uniform_filter1d(np.abs(W), size=max(3, int(len(W) * 0.02)))
    W = W / (sm + 1e-6 * sm.max()); W[(f < band[0]) | (f > band[1])] = 0
    return np.fft.irfft(W, len(w))


def pcc2(x, nlag):
    sig = np.exp(1j * np.angle(hilbert(x))); n = len(sig)
    S = np.fft.fft(sig, 2 * n)
    return 2.0 * np.real(np.fft.ifft(S * np.conj(S))[:nlag + 1]) / n


def days_for(serials, allpaths):
    days = {}
    for p in allpaths:
        b = os.path.basename(p)
        for S in serials:
            t = f"E{S}"
            if b.startswith(t):
                d = b[len(t):len(t) + 6]
                if d.isdigit():
                    days.setdefault(d, []).append(p)
                break
    return days


def process_day(code, day, files, nlag, nwin):
    cache = CACHE / f"{code}_{day}.npy"                      # (nbands, nlag+1) daily mean
    if cache.exists():
        return np.load(cache)
    import obspy
    st = obspy.Stream()
    for f in sorted(files):
        try:
            st += obspy.read(f)
        except Exception:
            pass
    if len(st) == 0:
        out = np.zeros((len(BANDS), nlag + 1)); np.save(cache, out); return out
    st.merge(method=1, fill_value=0); tr = st[0]
    tr.detrend("demean"); tr.detrend("linear")
    tr.filter("lowpass", freq=0.4 * FS_EFF, corners=4, zerophase=True)
    tr.decimate(int(DECI), no_filter=True)
    d0 = tr.data.astype(np.float64); fs = tr.stats.sampling_rate
    out = np.zeros((len(BANDS), nlag + 1))
    for bi, band in enumerate(BANDS):
        acs = []
        for i in range(0, len(d0) - nwin, nwin):
            w = d0[i:i + nwin]
            if np.std(w) < 1e-9:
                continue
            acs.append(pcc2(whiten(w, fs, band), nlag))
        if acs:
            out[bi] = np.mean(acs, 0)
    np.save(cache, out)
    return out


def stack_station(code, allpaths, max_days):
    days = days_for(STATIONS[code], allpaths)
    dl = sorted(days)[:max_days] if max_days else sorted(days)
    nlag, nwin = int(MAXLAG * FS_EFF), int(WIN * FS_EFF)
    acc = []
    for k, day in enumerate(dl):
        acc.append(process_day(code, day, days[day], nlag, nwin))
        if (k + 1) % 20 == 0:
            print(f"   [{code}] {k+1}/{len(dl)} days")
    A = np.array(acc)                                        # (ndays, nbands, nlag+1)
    lag = np.arange(nlag + 1) / FS_EFF
    stacks, cohs = [], []
    for bi in range(len(BANDS)):
        M = A[:, bi, :]
        coh = np.abs(np.exp(1j * np.angle(hilbert(M, axis=1))).mean(0))
        stacks.append(M.mean(0) * coh ** 2); cohs.append(coh)
    return lag, np.array(stacks), np.array(cohs), len(dl)


def band_stable_troughs(lag, stacks):
    """Troughs present (within +/-0.1 s) in ALL bands = real reflectors."""
    band = (lag >= TMIN) & (lag <= TMAX)
    per = []
    for s in stacks:
        cw = s.copy()
        tr = (cw[1:-1] < cw[:-2]) & (cw[1:-1] < cw[2:])
        ti = np.where(tr)[0] + 1
        ti = ti[band[ti] & (cw[ti] < 0)]
        per.append(set(np.round(lag[ti], 1)))
    stable = sorted(per[0].intersection(*per[1:]))
    return stable


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    ap = argparse.ArgumentParser(); ap.add_argument("--max-days", type=int, default=60)
    a = ap.parse_args()
    allpaths = INDEX.read_text().splitlines()
    s_rf = pd.read_csv(DATA / "sediment_rf.csv")
    codes = list(STATIONS)
    fig, axes = plt.subplots(1, len(codes), figsize=(3.5 * len(codes), 7), sharey=True)
    if len(codes) == 1:
        axes = [axes]
    rows = []
    cols = ["#1f77b4", "#2ca02c", "#d62728"]
    for ax, code in zip(axes, codes):
        lag, stacks, cohs, nd = stack_station(code, allpaths, a.max_days)
        m = (lag >= TMIN) & (lag <= TMAX)
        for bi, band in enumerate(BANDS):
            s = stacks[bi][m]; s = s / (np.max(np.abs(s)) + 1e-12)
            ax.plot(s + 0, lag[m], color=cols[bi], lw=1.0, label=f"{band[0]:g}-{band[1]:g} Hz")
        stable = band_stable_troughs(lag, stacks)
        # basement = strongest (deepest-weighted) band-stable trough
        base = None
        if stable:
            # strength = mean |coh-weighted stack| across bands at each stable twt
            strengths = []
            for t in stable:
                k = int(round(t * FS_EFF))
                strengths.append(np.mean([abs(stacks[bi][k] * cohs[bi][k]) for bi in range(len(BANDS))]))
            base = stable[int(np.argmax(strengths))]
        rf = s_rf[s_rf.code == code]
        h_rf = float(rf.h_sed_km.iloc[0]) if len(rf) and rf.h_sed_km.iloc[0] > 0 else None
        for t in stable:
            ax.axhline(t, color="gray", ls=":", lw=0.8)
        depth = base * VP / 2 if base else None
        if base:
            ax.axhline(base, color="k", lw=2)
            ax.text(-0.98, base - 0.1, f"AN basement\n{base:.2f}s\n{depth:.1f} km",
                    fontsize=8.5, fontweight="bold", va="bottom")
        if h_rf:
            ax.axhline(2 * h_rf / VP, color="purple", ls="--", lw=1.2)
            ax.text(0.2, 2 * h_rf / VP + 0.1, f"RF {h_rf:.1f}km", color="purple", fontsize=8)
        ax.set_ylim(TMAX, TMIN); ax.set_xlim(-1.05, 1.05); ax.set_xticks([])
        ax.set_title(f"{code} ({nd}d)", fontsize=10, fontweight="bold")
        ax.legend(fontsize=6.5, loc="lower right")
        rows.append((code, base, depth, base * VP_LO / 2 if base else None,
                     base * VP_HI / 2 if base else None, h_rf, ";".join(f"{t:.2f}" for t in stable)))
        print(f"  {code}: band-stable troughs {stable} -> basement {base}s")
    axes[0].set_ylabel("two-way time (s)")
    fig.suptitle("Central Java — RF-INDEPENDENT basement from multi-band AN autocorrelation\n"
                 "(band-stable reflectors survive; sidelobes move) — dotted = band-stable, "
                 "purple = RF cross-check", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(FIG / "basement_multiband.png", dpi=200); plt.close(fig)
    pd.DataFrame(rows, columns=["code", "an_twt_s", "an_depth_km", "depth_lo", "depth_hi",
                                "rf_depth_km", "stable_troughs_s"]).to_csv(
        DATA / "basement_multiband.csv", index=False)
    print("\nWrote basement_multiband.png +", DATA / "basement_multiband.csv")
    for c, tb, d, dlo, dhi, hrf, _ in rows:
        ds = f"{d:.1f}km ({dlo:.1f}-{dhi:.1f})" if d else "no stable pick"
        print(f"  {c}: AN {tb if tb else 'n/a'}s -> {ds} | RF {hrf}")


if __name__ == "__main__":
    main()
