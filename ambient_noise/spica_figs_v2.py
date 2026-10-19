"""
Improved Spica-style C1 figures for MERAMEX, rebuilt from the cached cross-
correlations (ambient_noise/cache_c1/c1_pairs.npz) - no reprocessing needed.

Fixes the old figure (Fig 9):
  * velocity gate restored to a PHYSICAL surface-wave window (1.8-4.0 km/s);
    the previous 0.6 km/s floor was catching zero-lag noise -> spurious ~1 km/s.
  * symmetric (causal+acausal folded) EGF to double SNR.
  * record section as a clean filled-wiggle gather + physical move-out lines.
  * dispersion shown as a proper 2-D FTAN energy diagram (period vs group
    velocity) summed over SNR-selected pairs, with a picked ridge + IQR band -
    the standard, informative presentation (cf. Spica et al. 2016, Fig 5).

Run (fbt):  python ambient_noise/spica_figs_v2.py
"""
from __future__ import annotations
import pathlib
import numpy as np
from scipy.signal import hilbert

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / "ambient_noise" / "cache_c1" / "c1_pairs.npz"
FIG = ROOT / "figures" / "ambient_noise"
BAND = (0.1, 0.3)

VMIN, VMAX = 1.8, 4.0          # physical Rayleigh group-velocity window (km/s)
PERIODS = np.linspace(3.5, 8.0, 24)   # trim long-period edge (array-length limited)
DMIN = 20.0                    # min inter-station distance for surface-wave sep.
SNR_MIN = 2.3


def load():
    z = np.load(CACHE)
    lag, dist, cc = z["lag"], z["dist"], z["cc"]
    nlag = (len(lag) - 1) // 2
    tsym = lag[nlag:]
    sym = 0.5 * (cc[:, nlag:] + cc[:, :nlag + 1][:, ::-1])  # fold -> symmetric
    return lag, dist, cc, tsym, sym


def snr_of(sym, tsym, dist):
    out = np.full(len(dist), np.nan)
    for i, d in enumerate(dist):
        t1, t2 = d / VMAX, d / VMIN
        sig = (tsym >= t1) & (tsym <= t2)
        noi = (tsym >= t2 + 40) & (tsym <= t2 + 120)
        if sig.sum() > 2 and noi.sum() > 5:
            out[i] = np.max(np.abs(sym[i, sig])) / (np.std(sym[i, noi]) + 1e-9)
    return out


def ftan_energy(s, t, dist, periods, vgrid):
    """FTAN envelope mapped to (period, velocity); normalised per period."""
    dt = t[1] - t[0]
    S = np.fft.rfft(s)
    f = np.fft.rfftfreq(len(s), dt)
    E = np.full((len(periods), len(vgrid)), np.nan)
    for i, T in enumerate(periods):
        f0 = 1.0 / T
        G = np.exp(-12.0 * ((f - f0) / f0) ** 2)
        env = np.abs(hilbert(np.fft.irfft(S * G, len(s))))
        tt = dist / vgrid                      # velocity -> arrival time
        good = (tt > t[1]) & (tt < t[-1])
        row = np.full(len(vgrid), np.nan)
        row[good] = np.interp(tt[good], t, env)
        m = np.nanmax(row)
        if m > 0:
            E[i] = row / m
    return E


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    lag, dist, cc, tsym, sym = load()
    snr = snr_of(sym, tsym, dist)
    print(f"{len(dist)} pairs, dist {dist.min():.0f}-{dist.max():.0f} km, "
          f"SNR median {np.nanmedian(snr):.2f}")

    # ================= (a) record section =================
    order = np.argsort(dist)
    bins = np.arange(0, dist.max() + 14, 14)
    bd, bs = [], []
    for b0, b1 in zip(bins[:-1], bins[1:]):
        m = (dist >= b0) & (dist < b1)
        if m.sum() == 0:
            continue
        w = np.clip(np.nan_to_num(snr[m]), 0.3, None)       # SNR-weighted stack
        stack = np.average(sym[m], axis=0, weights=w)
        bd.append(dist[m].mean()); bs.append(stack)
    bd = np.array(bd); bs = np.array(bs)

    fig, ax = plt.subplots(figsize=(6.6, 7.2))
    sc = 10.5
    for d, c in zip(bd, bs):
        n = c / (np.max(np.abs(c)) + 1e-12)
        y = n * sc + d
        ax.plot(tsym, y, color="k", lw=0.8)
        ax.fill_between(tsym, d, y, where=(n > 0), color="#C0392B", alpha=.85, lw=0)
        ax.fill_between(tsym, d, y, where=(n < 0), color="#2C5E8A", alpha=.55, lw=0)
    for v, cc_ in [(2.5, "#1A1A1A"), (3.0, "#1A6B3A")]:
        ax.plot(bd / v, bd, "--", color=cc_, lw=1.6, label=f"{v} km/s")
    ax.set_xlim(0, 65); ax.set_ylim(0, bd.max() + sc)
    ax.set_xlabel("correlation lag (s)", fontsize=11)
    ax.set_ylabel("inter-station distance (km)", fontsize=11)
    ax.set_title("(a) MERAMEX C1 symmetric EGF\n"
                 f"SNR-weighted, {BAND[0]}–{BAND[1]} Hz",
                 fontsize=12, fontweight="bold")
    ax.legend(title="Rayleigh move-out", loc="lower right", fontsize=9,
              framealpha=.95)
    ax.grid(alpha=.18)
    fig.tight_layout(); fig.savefig(FIG / "spica_record_section.png", dpi=220)
    plt.close(fig); print("Wrote spica_record_section.png")

    # ================= (b) 2-D FTAN dispersion =================
    vgrid = np.linspace(VMIN, VMAX, 160)
    sel = np.where((dist >= DMIN) & (snr >= SNR_MIN))[0]
    print(f"dispersion pairs (d>={DMIN:.0f} km, SNR>={SNR_MIN}): {len(sel)}")
    stackE = np.zeros((len(PERIODS), len(vgrid)))
    nE = np.zeros((len(PERIODS), len(vgrid)))
    picks = []
    for i in sel:
        E = ftan_energy(sym[i], tsym, dist[i], PERIODS, vgrid)
        ok = np.isfinite(E)
        stackE[ok] += E[ok]; nE[ok] += 1
    M = np.divide(stackE, np.maximum(nE, 1))
    M[nE < max(3, 0.2 * len(sel))] = np.nan
    # ridge pick (energy-weighted centroid near the max -> smooth, stable)
    vpick = np.full(len(PERIODS), np.nan)
    for j in range(len(PERIODS)):
        row = M[j]
        if np.isfinite(row).any():
            k = np.nanargmax(row)
            lo, hi = max(0, k - 12), min(len(vgrid), k + 13)
            seg = np.nan_to_num(row[lo:hi])
            vpick[j] = np.sum(vgrid[lo:hi] * seg) / (seg.sum() + 1e-12)
    # light smoothing of the picked curve
    from scipy.ndimage import uniform_filter1d
    good = np.isfinite(vpick)
    vpick[good] = uniform_filter1d(vpick[good], size=3)
    # per-period (column) normalisation for display so the ridge is visible
    Mdisp = M.copy()
    for j in range(len(PERIODS)):
        row = Mdisp[j]
        if np.isfinite(row).any():
            lo, hi = np.nanmin(row), np.nanmax(row)
            if hi > lo:
                Mdisp[j] = (row - lo) / (hi - lo)
    allv = []
    for i in sel:
        E = ftan_energy(sym[i], tsym, dist[i], PERIODS, vgrid)
        vp = np.array([vgrid[np.nanargmax(E[j])] if np.isfinite(E[j]).any() else np.nan
                       for j in range(len(PERIODS))])
        allv.append(vp)
    allv = np.array(allv)
    q1 = np.nanpercentile(allv, 25, axis=0); q3 = np.nanpercentile(allv, 75, axis=0)

    ccmap = LinearSegmentedColormap.from_list(
        "ftan", ["#FFFFFF", "#D7E8F2", "#6BA8CF", "#2E6DA4", "#1A3E6B", "#0A1A33"])
    fig, ax = plt.subplots(figsize=(7.4, 7.2))
    pm = ax.pcolormesh(PERIODS, vgrid, Mdisp.T, cmap=ccmap, shading="gouraud",
                       vmin=0, vmax=1)
    ok = np.isfinite(vpick)
    ax.fill_between(PERIODS[ok], q1[ok], q3[ok], color="#C0392B", alpha=.18,
                    label="inter-quartile range")
    ax.plot(PERIODS[ok], vpick[ok], color="#C0392B", lw=3.2, marker="o", ms=4,
            label="picked group velocity")
    cb = fig.colorbar(pm, ax=ax, pad=.02)
    cb.set_label("FTAN energy (normalised per period)", fontsize=10)
    ax.set_xlim(PERIODS.min(), PERIODS.max()); ax.set_ylim(VMIN, VMAX)
    ax.set_xlabel("period (s)", fontsize=11)
    ax.set_ylabel("Rayleigh group velocity (km/s)", fontsize=11)
    ax.set_title("(b) Rayleigh group-velocity dispersion\n"
                 f"FTAN energy stack, {len(sel)} pairs",
                 fontsize=12, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9, framealpha=.95)
    fig.tight_layout(); fig.savefig(FIG / "spica_dispersion.png", dpi=220)
    plt.close(fig); print("Wrote spica_dispersion.png")
    if ok.sum():
        print("picked Vg (km/s) at 4/5/6/7/8 s:",
              [round(float(np.interp(t, PERIODS[ok], vpick[ok])), 2)
               for t in (4, 5, 6, 7, 8)])


if __name__ == "__main__":
    main()
