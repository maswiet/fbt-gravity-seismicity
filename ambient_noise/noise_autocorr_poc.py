"""
Proof-of-concept: single-station ambient-noise autocorrelation for Central Java
basement imaging with MERAMEX data — following Romero & Schimmel (2018, JGR).

Reads the raw EDL continuous vertical recordings (obspy reads .PRI0 natively,
100 Hz), pre-processes 30-min windows, and forms the zero-offset P reflection
response by AUTOCORRELATION, using both:
  * CCGN  — classical, energy-normalised autocorrelation
  * PCC   — phase cross-correlation (Schimmel 1999), amplitude-unbiased
    (for power nu=2 this reduces to the mean cos of the instantaneous-phase
     difference, computed here by FFT autocorrelation of unit phasors)
stacked linearly and with a phase-weighted stack (PWS; Schimmel & Paulssen 1997).

The stacked autocorrelogram's first strong arrival is the two-way P traveltime
to the basement; with a sediment Vp it maps to depth and is compared with the
RF sediment thickness at the station (our a-priori control, in place of wells).

Run (fbt env):  python ambient_noise/noise_autocorr_poc.py --station BI4 --doy 260
"""
from __future__ import annotations
import sys, glob, argparse, pathlib
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
MER = pathlib.Path("/Volumes/Untitled/MERAMEX DATA")
FIG = ROOT / "figures" / "ambient_noise"; FIG.mkdir(parents=True, exist_ok=True)
INFO = MER / "DOY 260_1905" / "INFO.DAT"
FS = 100.0
BAND = (0.8, 8.0)          # basement band (Hz)
WIN = 1800                 # window length (s) = 30-min segment
MAXLAG = 8.0               # autocorrelogram half-length (s)
RF_SED = {"BI4": 6.64, "AF1": None, "AI4": None}   # RF sediment thickness (km)
VP_SED = 3.0               # sediment Vp (km/s) for TWT<->depth


def station_serial(code):
    for ln in INFO.read_text(errors="ignore").splitlines():
        p = ln.split()
        if len(p) > 9 and p[7] == code:
            return p[0], float(p[8]), float(p[9])     # serial, lat, lon
    raise SystemExit(f"station {code} not in INFO.DAT")


def read_day_z(code, doy):
    import obspy
    serial, lat, lon = station_serial(code)
    d = MER / "DOY 260_1905" / code / str(doy)
    files = sorted(glob.glob(str(d / f"E{serial}*.PRI0")))
    if not files:
        files = sorted(glob.glob(str(d / "*.PRI0")))
    print(f"{code}: serial {serial}  ({lat},{lon})  {len(files)} vertical segments")
    st = obspy.Stream()
    for f in files:
        try:
            st += obspy.read(f)
        except Exception:
            pass
    st.merge(method=1, fill_value=0)
    return st, lat, lon


def preprocess(tr):
    tr = tr.copy()
    tr.detrend("demean"); tr.detrend("linear"); tr.taper(0.02)
    tr.filter("bandpass", freqmin=BAND[0], freqmax=BAND[1], corners=4, zerophase=True)
    return tr.data.astype(np.float64)


def whiten_1bit(x):
    x = x - x.mean()
    # temporal normalisation: 1-bit (robust to transients/earthquakes)
    return np.sign(x)


def autocorr_ccgn(x, nlag):
    n = len(x)
    X = np.fft.rfft(x, 2 * n)
    ac = np.fft.irfft(X * np.conj(X))[:nlag + 1]
    return ac / (ac[0] + 1e-12)


def autocorr_pcc2(x, nlag):
    """PCC power nu=2 == mean cos of instantaneous-phase difference (FFT of phasors)."""
    from scipy.signal import hilbert
    sig = np.exp(1j * np.angle(hilbert(x)))
    n = len(sig)
    S = np.fft.fft(sig, 2 * n)
    ac = np.fft.ifft(S * np.conj(S))[:nlag + 1]
    return 2.0 * np.real(ac) / n


def pws(traces, nu=2):
    """Phase-weighted stack of a list of equal-length traces."""
    from scipy.signal import hilbert
    A = np.array(traces)
    lin = A.mean(0)
    phasors = np.exp(1j * np.angle(hilbert(A, axis=1)))
    coh = np.abs(phasors.mean(0))
    return lin * coh ** nu, lin, coh


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--station", default="BI4"); ap.add_argument("--doy", default="260")
    a = ap.parse_args()
    st, lat, lon = read_day_z(a.station, a.doy)
    if len(st) == 0:
        raise SystemExit("no data read")
    tr = st[0]
    print(f"  merged: {tr.stats.starttime} .. {tr.stats.endtime}  {tr.stats.npts} pts @ {tr.stats.sampling_rate} Hz")
    data = preprocess(tr)
    nlag = int(MAXLAG * FS)
    nwin = int(WIN * FS)
    ccgn, pccs = [], []
    for i in range(0, len(data) - nwin, nwin):
        w = data[i:i + nwin]
        if np.std(w) < 1e-9:
            continue
        ccgn.append(autocorr_ccgn(whiten_1bit(w), nlag))
        pccs.append(autocorr_pcc2(w, nlag))
    print(f"  windows stacked: {len(ccgn)}")
    lag = np.arange(nlag + 1) / FS
    ccgn_pws, ccgn_lin, _ = pws(ccgn)
    pcc_pws, pcc_lin, coh = pws(pccs)

    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for a_, lin, pw, name, c in [(ax[0], ccgn_lin, ccgn_pws, "CCGN (classical)", "#065A82"),
                                 (ax[1], pcc_lin, pcc_pws, "PCC ν=2 (phase)", "#B0512F")]:
        a_.plot(lag, lin / np.max(np.abs(lin[10:])), color=c, lw=1, alpha=.5, label="linear stack")
        a_.plot(lag, pw / np.max(np.abs(pw[10:]) + 1e-9), color=c, lw=2, label="phase-weighted stack")
        a_.set_ylabel("norm. amplitude"); a_.set_title(
            f"{a.station} — stacked autocorrelation ({name}), DOY {a.doy}, band {BAND[0]}–{BAND[1]} Hz",
            fontsize=11, fontweight="bold")
        a_.grid(alpha=.3); a_.legend(fontsize=9, loc="upper right")
        h = RF_SED.get(a.station)
        if h:
            twt = 2 * h / VP_SED
            a_.axvline(twt, color="green", ls="--", lw=1.6)
            a_.text(twt + 0.05, 0.7, f"RF basement\n2H/Vp = {twt:.1f} s\n(H={h} km)",
                    color="green", fontsize=9)
    ax[1].set_xlabel("autocorrelation lag = two-way time (s)"); ax[1].set_xlim(0, MAXLAG)
    fig.suptitle("MERAMEX ambient-noise autocorrelation — proof of concept "
                 "(Romero & Schimmel 2018 workflow)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out = FIG / f"noise_autocorr_{a.station}_doy{a.doy}.png"
    fig.savefig(out, dpi=200); print("Wrote", out)


if __name__ == "__main__":
    main()
