"""
Full single-station ambient-noise autocorrelation pipeline for the MERAMEX
flagship stations (BI4, AF1, AI4, BG2) — Romero & Schimmel (2018) workflow.

For each station it reads the raw EDL continuous vertical data (obspy, 100 Hz)
day by day, band-passes, computes the PCC (phase cross-correlation, nu=2) auto-
correlation per 30-min window, and stacks over ALL processed days both linearly
and with a phase-weighted stack (PWS). Per-day window autocorrelations are cached
to .npy so the run is resumable and days can be added incrementally.

The stacked autocorrelogram's first coherent arrival is the two-way P traveltime
to the basement; it is compared with 2H/Vp from the RF sediment thickness at the
station (a-priori control, replacing Romero & Schimmel's well data).

Build the file index once (slow, external disk), then run:
  find "/Volumes/Untitled/MERAMEX DATA" -name '*.PRI0' > ambient_noise/pri0_index.txt
  python ambient_noise/run_pipeline.py --max-days 45
"""
from __future__ import annotations
import sys, os, glob, argparse, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
MER = pathlib.Path("/Volumes/Untitled/MERAMEX DATA")
INFO = MER / "DOY 260_1905" / "INFO.DAT"
INDEX = ROOT / "ambient_noise" / "pri0_index.txt"
CACHE = ROOT / "ambient_noise" / "cache"; CACHE.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "figures" / "ambient_noise"; FIG.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "data" / "processed" / "rf_java"

FS = 100.0
BAND = (0.8, 8.0)
WIN = 1800
MAXLAG = 8.0
VP_SED = 3.0
STATIONS = {"BI4": ["3080"], "AF1": ["3135"], "AI4": ["3043", "3092"], "BG2": ["3121"]}


def station_meta(code):
    lat = lon = None
    for ln in INFO.read_text(errors="ignore").splitlines():
        p = ln.split()
        if len(p) > 9 and p[7] == code:
            lat, lon = float(p[8]), float(p[9]); break
    return lat, lon


def rf_thickness(code):
    import pandas as pd
    s = pd.read_csv(DATA / "sediment_rf.csv")
    r = s[s.code == code]
    return float(r.h_sed_km.iloc[0]) if len(r) and r.h_sed_km.iloc[0] > 0 else None


def index_paths():
    if not INDEX.exists():
        raise SystemExit(f"Missing {INDEX}. Build it once with:\n"
                         f"  find \"{MER}\" -name '*.PRI0' > {INDEX}")
    return INDEX.read_text().splitlines()


def days_for(serials, allpaths):
    """Map YYMMDD -> list of file paths, for the given serial(s)."""
    days = {}
    for pth in allpaths:
        base = os.path.basename(pth)
        for S in serials:
            tag = f"E{S}"
            if base.startswith(tag):
                day = base[len(tag):len(tag) + 6]
                if day.isdigit():
                    days.setdefault(day, []).append(pth)
                break
    return days


def autocorr_pcc2(x, nlag):
    from scipy.signal import hilbert
    sig = np.exp(1j * np.angle(hilbert(x)))
    n = len(sig)
    S = np.fft.fft(sig, 2 * n)
    ac = np.fft.ifft(S * np.conj(S))[:nlag + 1]
    return 2.0 * np.real(ac) / n


def process_day(code, day, files, nlag, nwin):
    cache = CACHE / f"{code}_{day}.npy"
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
        np.save(cache, np.zeros((0, nlag + 1))); return np.load(cache)
    st.merge(method=1, fill_value=0)
    tr = st[0]
    tr.detrend("demean"); tr.detrend("linear")
    tr.filter("bandpass", freqmin=BAND[0], freqmax=BAND[1], corners=4, zerophase=True)
    d = tr.data.astype(np.float64)
    acs = []
    for i in range(0, len(d) - nwin, nwin):
        w = d[i:i + nwin]
        if np.std(w) < 1e-9:
            continue
        acs.append(autocorr_pcc2(w, nlag))
    arr = np.array(acs) if acs else np.zeros((0, nlag + 1))
    np.save(cache, arr)
    return arr


def pws(A, nu=2):
    from scipy.signal import hilbert
    lin = A.mean(0)
    ph = np.exp(1j * np.angle(hilbert(A, axis=1)))
    coh = np.abs(ph.mean(0))
    return lin * coh ** nu, lin, coh


def run_station(code, allpaths, max_days):
    lat, lon = station_meta(code)
    h_rf = rf_thickness(code)
    days = days_for(STATIONS[code], allpaths)
    daylist = sorted(days)[:max_days] if max_days else sorted(days)
    nlag, nwin = int(MAXLAG * FS), int(WIN * FS)
    print(f"[{code}] serial {STATIONS[code]} ({lat},{lon})  {len(days)} days available, "
          f"processing {len(daylist)}; RF sed = {h_rf} km")
    allacs = []
    for k, day in enumerate(daylist):
        arr = process_day(code, day, days[day], nlag, nwin)
        if arr.shape[0]:
            allacs.append(arr)
        if (k + 1) % 10 == 0:
            print(f"   ...{k+1}/{len(daylist)} days, windows so far "
                  f"{sum(a.shape[0] for a in allacs)}")
    if not allacs:
        print(f"   [{code}] no windows"); return None
    A = np.vstack(allacs)
    pw, lin, coh = pws(A)
    lag = np.arange(nlag + 1) / FS
    return dict(code=code, lat=lat, lon=lon, h_rf=h_rf, lag=lag, lin=lin, pws=pw,
                nwin=A.shape[0], ndays=len(daylist))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=45)
    ap.add_argument("--stations", default="BI4,AF1,AI4,BG2")
    a = ap.parse_args()
    allpaths = index_paths()
    print(f"index: {len(allpaths)} PRI0 files")
    res = []
    for code in a.stations.split(","):
        r = run_station(code, allpaths, a.max_days)
        if r:
            res.append(r)
            np.savez(CACHE / f"stack_{code}.npz", **{k: r[k] for k in
                     ["lag", "lin", "pws", "h_rf", "nwin", "ndays"]})

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(res)
    fig, axes = plt.subplots(n, 1, figsize=(11, 2.4 * n), sharex=True)
    if n == 1:
        axes = [axes]
    for ax, r in zip(axes, res):
        pw = r["pws"] / (np.max(np.abs(r["pws"][10:])) + 1e-12)
        ln = r["lin"] / (np.max(np.abs(r["lin"][10:])) + 1e-12)
        ax.plot(r["lag"], ln, color="#9AB", lw=1, alpha=.7, label="linear")
        ax.plot(r["lag"], pw, color="#065A82", lw=1.8, label="phase-weighted")
        ax.axhline(0, color="gray", lw=.5)
        if r["h_rf"]:
            twt = 2 * r["h_rf"] / VP_SED
            ax.axvline(twt, color="#B0512F", ls="--", lw=1.6)
            ax.text(twt + 0.06, 0.6, f"RF: 2H/Vp={twt:.1f}s\nH={r['h_rf']}km",
                    color="#B0512F", fontsize=8.5, va="center")
        ax.set_ylabel("norm. amp"); ax.grid(alpha=.3)
        ax.set_title(f"{r['code']}  —  PCC autocorrelation, {r['ndays']} days / "
                     f"{r['nwin']} windows stacked", fontsize=10.5, fontweight="bold")
        ax.legend(fontsize=8, loc="upper right")
    axes[-1].set_xlabel("autocorrelation lag = two-way time (s)"); axes[-1].set_xlim(0, MAXLAG)
    fig.suptitle("MERAMEX flagship stations — ambient-noise autocorrelation "
                 f"(PCC + PWS, band {BAND[0]}–{BAND[1]} Hz)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out = FIG / "noise_autocorr_flagship.png"
    fig.savefig(out, dpi=200); print("Wrote", out)


if __name__ == "__main__":
    main()
