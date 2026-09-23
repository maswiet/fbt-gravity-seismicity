"""
Spica et al. (2016, GJI) ambient-noise CROSS-correlation (C1) applied to MERAMEX
Central Java, and compared with the Romero & Schimmel autocorrelation method.

Spica's method: cross-correlate the vertical ambient noise between station PAIRS
to retrieve the empirical Green's function (Rayleigh surface wave), measure the
group-velocity DISPERSION (FTAN) and invert for Vs. (C3 = correlation of the coda
of C1 bridges asynchronous networks - not needed here since MERAMEX is one
synchronous array.)  This is complementary to Romero & Schimmel, whose single-
station AUTOcorrelation gives the body-wave basement REFLECTION (depth), not the
velocity.

This script computes C1 for a subset of the dense MERAMEX array and produces:
  spica_record_section.png   EGF vs inter-station distance (Rayleigh move-out)  ~ Spica Fig 5a
  spica_dispersion.png       Rayleigh group-velocity dispersion (FTAN)          ~ Spica Fig 5d

Run (fbt):  python ambient_noise/spica_c1.py --n-sta 34 --max-days 20
"""
from __future__ import annotations
import sys, os, argparse, pathlib
import numpy as np
from scipy.signal import hilbert
from scipy.ndimage import uniform_filter1d

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ambient_noise"))
import basement_map as BM                 # station_table, INDEX
import multiband_basement as MBB           # days_for
CACHE = ROOT / "ambient_noise" / "cache_c1"; CACHE.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "figures" / "ambient_noise"; FIG.mkdir(parents=True, exist_ok=True)

FS, DECI = 100.0, 20
FS_EFF = FS / DECI                        # 5 Hz
BAND = (0.1, 0.3)                         # Hz (~3.3-10 s) secondary-microseism band
WIN = 3600                                # 1-hour segments (Spica)
MAXLAG = 250.0                            # s
BTAG = f"b{BAND[0]:g}-{BAND[1]:g}"


def pws_stack(A, nu=2):
    """Phase-weighted stack of rows of A (Schimmel & Paulssen 1997)."""
    A = np.asarray(A)
    if A.ndim == 1 or A.shape[0] == 1:
        return A.reshape(-1)
    lin = A.mean(0)
    ph = np.exp(1j * np.angle(hilbert(A, axis=1)))
    coh = np.abs(ph.mean(0))
    return lin * coh ** nu


def geodist(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1); dl = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))


def whiten(w, fs, band):
    w = w - w.mean()
    env = uniform_filter1d(np.abs(w), size=max(1, int(fs)))
    w = w / (env + 1e-9*env.max())        # 1-bit-like temporal normalisation
    W = np.fft.rfft(w); f = np.fft.rfftfreq(len(w), 1.0/fs)
    sm = uniform_filter1d(np.abs(W), size=max(3, int(len(W)*0.01)))
    W = W/(sm + 1e-6*sm.max()); W[(f < band[0]) | (f > band[1])] = 0
    return np.fft.irfft(W, len(w))


def day_trace(code, day, files):
    """Whitened, decimated, hour-normalised full-day vertical trace (cached)."""
    cache = CACHE / f"{code}_{day}_{BTAG}.npy"
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
        np.save(cache, np.zeros(0)); return np.load(cache)
    st.merge(method=1, fill_value=0); tr = st[0]
    tr.detrend("demean"); tr.detrend("linear")
    tr.filter("lowpass", freq=0.4*FS_EFF, corners=4, zerophase=True)
    tr.decimate(int(DECI), no_filter=True)
    tr.filter("bandpass", freqmin=BAND[0], freqmax=BAND[1], corners=4, zerophase=True)
    d = tr.data.astype(np.float64); fs = tr.stats.sampling_rate
    nwin = int(WIN*fs); out = np.zeros_like(d)
    for i in range(0, len(d)-nwin+1, nwin):
        out[i:i+nwin] = whiten(d[i:i+nwin], fs, BAND)
    np.save(cache, out); return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-sta", type=int, default=34)
    ap.add_argument("--max-days", type=int, default=0)   # 0 = all days
    a = ap.parse_args()
    allpaths = BM.INDEX.read_text().splitlines()
    tab = BM.station_table()
    # choose n-sta stations spread over the array (by sorting on lon then subsampling)
    items = sorted(tab.items(), key=lambda kv: (kv[1][1], kv[1][0]))
    step = max(1, len(items)//a.n_sta)
    chosen = items[::step][:a.n_sta]
    print(f"stations chosen: {len(chosen)} of {len(tab)}")

    # load day traces per station
    nlag = int(MAXLAG*FS_EFF)
    data = {}
    for code, (lat, lon, serials) in chosen:
        days = MBB.days_for(serials, allpaths)
        dl = sorted(days)[:a.max_days] if a.max_days else sorted(days)
        traces = [day_trace(code, dy, days[dy]) for dy in dl]
        traces = [t for t in traces if t.size > int(3600*FS_EFF)]
        if traces:
            data[code] = (lat, lon, traces)
    codes = list(data)
    print(f"stations with data: {len(codes)}")

    # C1 cross-correlations, stacked over common days (by index)
    pairs = []
    for i in range(len(codes)):
        for j in range(i+1, len(codes)):
            a_, b_ = codes[i], codes[j]
            (la, lo, ta), (lb, lob, tb_) = data[a_], data[b_]
            nd = min(len(ta), len(tb_))
            if nd == 0:
                continue
            daily = []
            for k in range(nd):
                x, y = ta[k], tb_[k]
                n = min(len(x), len(y))
                if n < int(3600*FS_EFF):
                    continue
                X = np.fft.rfft(x[:n]); Y = np.fft.rfft(y[:n])
                cc = np.fft.irfft(X*np.conj(Y))
                cc = np.concatenate([cc[-nlag:], cc[:nlag+1]])   # -lag..+lag
                daily.append(cc / (np.std(cc)+1e-12))
            if not daily:
                continue
            egf = pws_stack(np.array(daily))                     # phase-weighted stack over days
            dist = geodist(la, lo, lb, lob)
            pairs.append((dist, egf))
    pairs.sort(key=lambda p: p[0])
    print(f"pairs: {len(pairs)}, dist {pairs[0][0]:.0f}-{pairs[-1][0]:.0f} km")
    lag = (np.arange(2*nlag+1)-nlag)/FS_EFF
    np.savez(CACHE/"c1_pairs.npz", lag=lag,
             dist=np.array([d for d, _ in pairs]),
             cc=np.array([c for _, c in pairs]))
    make_figs(lag, pairs)


VMIN, VMAX = 0.6, 3.2                      # physical group-velocity window (km/s)


def make_figs(lag, pairs):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    dists = np.array([d for d, _ in pairs])
    ccs = np.array([c for _, c in pairs])
    nlag = (len(lag)-1)//2
    # --- distance-bin phase-weighted stacks (boost the coherent EGF) ---
    bins = np.arange(0, dists.max()+12, 12)
    bd, bs = [], []
    for b0, b1 in zip(bins[:-1], bins[1:]):
        m = (dists >= b0) & (dists < b1)
        if m.sum() < 2:
            continue
        bd.append(dists[m].mean()); bs.append(pws_stack(ccs[m]))
    bd = np.array(bd); bs = np.array(bs)
    tsym = lag[nlag:]; sym = 0.5*(bs[:, nlag:] + bs[:, :nlag+1][:, ::-1])

    # ---- record section (Spica Fig 5a) ----
    fig, ax = plt.subplots(figsize=(8.5, 8))
    for d, c in zip(bd, bs):
        n = c/(np.max(np.abs(c))+1e-9)
        ax.plot(lag, n*9 + d, color="k", lw=0.8)
        ax.fill_between(lag, d, n*9 + d, where=(n > 0), color="#B0512F", lw=0, alpha=.7)
    for v, cix in [(2.5, "#065A82"), (1.5, "#0A7D5A"), (0.8, "#888")]:
        ax.plot(bd/v, bd, "--", color=cix, lw=1.4, label=f"{v} km/s")
        ax.plot(-bd/v, bd, "--", color=cix, lw=1.4)
    ax.set_xlim(-140, 140); ax.set_ylim(0, bd.max()*1.03)
    ax.set_xlabel("correlation lag (s)"); ax.set_ylabel("inter-station distance (km)")
    ax.set_title(f"MERAMEX C1 EGF — distance-binned PWS, {BAND[0]}–{BAND[1]} Hz (cf. Spica Fig 5a)",
                 fontweight="bold", fontsize=12)
    ax.legend(title="apparent Vg", loc="upper right", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG/"spica_record_section.png", dpi=200); plt.close(fig)
    print("Wrote spica_record_section.png")

    # ---- FTAN group-velocity dispersion (physical velocity window) ----
    periods = np.linspace(3.5, 9.0, 24)
    fig, ax = plt.subplots(figsize=(8.5, 6))
    allgv = []
    for dm, s in zip(bd, sym):
        if dm < 25:
            continue
        gv = ftan_group_velocity(s, tsym, dm, periods)
        allgv.append(gv)
        ax.plot(periods, gv, color="#065A82", lw=0.9, alpha=.55)
    allgv = np.array(allgv); mean = np.nanmedian(allgv, 0)
    ax.plot(periods, mean, color="#B0512F", lw=3, label="median dispersion")
    ax.set_xlabel("period (s)"); ax.set_ylabel("Rayleigh group velocity (km/s)")
    ax.set_ylim(VMIN, VMAX); ax.grid(alpha=.3); ax.legend(fontsize=10)
    ax.set_title(f"MERAMEX C1 — Rayleigh group-velocity dispersion (FTAN, {BAND[0]}–{BAND[1]} Hz)",
                 fontweight="bold", fontsize=12)
    fig.tight_layout(); fig.savefig(FIG/"spica_dispersion.png", dpi=200); plt.close(fig)
    print("Wrote spica_dispersion.png")
    ok = np.isfinite(mean)
    if ok.sum():
        print("median group velocity (km/s) at 4/5/6/7/8 s:",
              [round(float(np.interp(t, periods[ok], mean[ok])), 2) for t in (4, 5, 6, 7, 8)])


def ftan_group_velocity(s, t, dist, periods):
    """Group velocity vs period: envelope peak within the physical velocity window."""
    dt = t[1]-t[0]; gv = np.full(len(periods), np.nan)
    S = np.fft.rfft(s); f = np.fft.rfftfreq(len(s), dt)
    tmin, tmax = dist/VMAX, dist/VMIN                       # velocity gate
    win = (t >= tmin) & (t <= tmax)
    if win.sum() == 0:
        return gv
    for i, T in enumerate(periods):
        f0 = 1.0/T
        G = np.exp(-8.0*((f-f0)/f0)**2)
        env = np.abs(hilbert(np.fft.irfft(S*G, len(s))))
        seg = np.where(win, env, -1)
        tg = t[np.argmax(seg)]
        if tg > 0:
            gv[i] = dist/tg
    return gv


if __name__ == "__main__":
    main()
