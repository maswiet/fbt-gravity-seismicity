"""
Tahap 2 — Receiver functions from the MERAMEX ARTHA event windows.

For every land station x matched event: read the 3-component GCF window, compute
back-azimuth / P onset / ray parameter (TauP iasp91) from station+event
geometry, rotate NE->RT, and deconvolve the radial by the vertical with the
iterative time-domain method (Ligorria & Ammon 1999 — the same algorithm as CPS
`saciterd`). Quality-control, stack per station, and save:

  data/processed/rf_java/rf/<STA>_rf.sac        (station-stacked radial RF, for rftn96)
  data/processed/rf_java/rf/<STA>_event_rfs.h5  (individual radial RFs)
  data/processed/rf_java/rf_summary.csv
  figures/rf_java/rf_demo_<STA>.png             (a QC receiver-function section)

Run:  python rf_gravity_java/compute_rf.py [--demo STA]
"""
from __future__ import annotations

import glob
import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C

TSHIFT = 10.0          # s of RF before P (time shift)
RF_LEN = 30.0          # s of RF after P kept for output/inversion


def _load_3c(code, doy):
    """Load the 3-component ARTHA window for a station code + DOY as a Stream."""
    import obspy
    comp_map = {"z": "BHZ", "n": "BHN", "e": "BHE"}
    st = obspy.Stream()
    for c, ch in comp_map.items():
        fs = glob.glob(str(C.ARTHA_DIR / f"{code.lower()}{c}_{doy}"))
        if not fs:
            return None
        tr = obspy.read(fs[0])[0]
        tr.stats.network = "XM"; tr.stats.station = code; tr.stats.channel = ch
        tr.stats.location = ""
        st += tr
    # Align to common time span & sampling.
    st.merge(method=1, fill_value=0)
    return st


def _set_geom(st, slat, slon, selev, ev):
    """Fill onset/back_azimuth/slowness/distance on each trace via TauP."""
    from obspy.geodetics import gps2dist_azimuth, locations2degrees
    from obspy.taup import TauPyModel
    import obspy
    model = TauPyModel("iasp91")
    dist = locations2degrees(slat, slon, ev["evlat"], ev["evlon"])
    _, _, baz = gps2dist_azimuth(slat, slon, ev["evlat"], ev["evlon"])
    arr = model.get_travel_times(source_depth_in_km=max(ev["evdepth_km"], 0),
                                 distance_in_degree=dist, phase_list=["P", "Pdiff"])
    if not arr:
        return None
    a = arr[0]
    onset = obspy.UTCDateTime(ev["origin_time"]) + a.time
    for tr in st:
        tr.stats.onset = onset
        tr.stats.back_azimuth = baz
        tr.stats.distance = dist
        tr.stats.slowness = a.ray_param_sec_degree            # s/deg
        tr.stats.inclination = a.incident_angle
        tr.stats.station_latitude = slat
        tr.stats.station_longitude = slon
        tr.stats.station_elevation = selev
        tr.stats.event_latitude = ev["evlat"]
        tr.stats.event_longitude = ev["evlon"]
        tr.stats.event_depth = ev["evdepth_km"]
    return dict(dist=dist, baz=baz, rayp_skm=a.ray_param_sec_degree / 111.19)


def _quality_ok(rtr):
    """Basic RF QC: finite, peak near zero-lag positive, bounded amplitude."""
    d = rtr.data
    if not np.all(np.isfinite(d)) or np.max(np.abs(d)) == 0:
        return False
    dt = rtr.stats.delta
    i0 = int(round(TSHIFT / dt))
    # direct-P peak should be the max within +/-2 s of zero lag and positive
    w = d[max(0, i0 - int(2/dt)): i0 + int(2/dt)]
    if w.size == 0 or np.max(w) <= 0:
        return False
    if np.max(w) < 0.3 * np.max(np.abs(d)):      # P conversion not dominant -> noisy
        return False
    return True


def compute_station(code, slat, slon, selev, events, gauss):
    """Return (list of good radial RF traces, list of ray params) for one station."""
    from rf import RFStream
    rfs, rayps, meta = [], [], []
    for _, ev in events.iterrows():
        st = _load_3c(code, int(ev["doy"]))
        if st is None or len(st) < 3:
            continue
        g = _set_geom(st, slat, slon, selev, ev)
        if g is None:
            continue
        try:
            rfst = RFStream(st)
            rfst.detrend("linear"); rfst.taper(0.05)
            rfst.filter("bandpass", freqmin=C.BP_CORNERS[0],
                        freqmax=C.BP_CORNERS[1], zerophase=True)
            rfst.resample(C.RF_SAMPLING)
            rfst.trim2(-TSHIFT - 5, RF_LEN + 30, reftime="onset")
            rfst.rf("P", rotate="NE->RT", deconvolve="iterative", gauss=gauss,
                    itmax=C.RF_ITERATIONS, minderr=0.001)
            rad = [tr for tr in rfst if tr.stats.channel.endswith("R")]
            if not rad:
                continue
            rtr = rad[0]
            aligned = _align_to_P(rtr)              # P exactly at t=TSHIFT
            if aligned is not None and _quality_ok(aligned):
                aligned.stats.rayp_skm = g["rayp_skm"]
                aligned.stats.baz = g["baz"]
                aligned.stats.dist = g["dist"]
                rfs.append(aligned); rayps.append(g["rayp_skm"])
                meta.append((int(ev["doy"]), g["baz"], g["dist"], g["rayp_skm"]))
        except Exception:
            continue
    return rfs, rayps, meta


def _align_to_P(rtr):
    """Slice a radial RF so the direct-P peak sits exactly at t=TSHIFT.

    Finds the dominant positive peak within +/-3 s of the theoretical onset and
    re-windows to [peak-TSHIFT, peak+RF_LEN]. Returns a Trace or None.
    """
    dt = rtr.stats.delta
    n = len(rtr.data)
    onset_idx = int(round((rtr.stats.onset - rtr.stats.starttime) / dt))
    w = int(3 / dt)
    lo, hi = max(0, onset_idx - w), min(n, onset_idx + w)
    if hi <= lo:
        return None
    ip = lo + int(np.argmax(rtr.data[lo:hi]))
    a = ip - int(round(TSHIFT / dt))
    b = ip + int(round(RF_LEN / dt))
    if a < 0 or b > n:
        return None
    out = rtr.copy()
    out.data = rtr.data[a:b].astype(float)
    out.stats.starttime = rtr.stats.starttime + a * dt
    return out


def main():
    import pandas as pd
    import obspy
    C.ensure_dirs()
    sta = pd.read_csv(C.STATIONS_CSV)
    land = sta[sta.kind.isin(["EDL", "SAM"])].reset_index(drop=True)
    events = pd.read_csv(C.DATA_PROCESSED / "events.csv")
    demo = None
    if "--demo" in sys.argv:
        demo = sys.argv[sys.argv.index("--demo") + 1].upper()

    rows = []
    for _, s in land.iterrows():
        code = s["code"]
        rfs, rayps, meta = compute_station(code, s["lat"], s["lon"],
                                           s["elev_m"], events, C.RF_GAUSS_CRUST)
        if len(rfs) == 0:
            continue
        # Stack (mean) the good radial RFs -> station RF for inversion.
        arrs = np.vstack([r.data[:min(len(x.data) for x in rfs)] for r in rfs])
        stack = arrs.mean(axis=0)
        strr = rfs[0].copy(); strr.data = stack
        strr.stats.rayp_skm = float(np.mean(rayps))
        out = C.RF_DIR / f"{code}_rf.sac"
        # SAC header: b = -TSHIFT, user0 = gauss, user4 = rayp (s/km), user5 = nrf
        strr.stats.sac = dict(b=-TSHIFT, user0=C.RF_GAUSS_CRUST,
                              user4=float(np.mean(rayps)), user5=len(rfs),
                              stla=s["lat"], stlo=s["lon"])
        strr.write(str(out), format="SAC")
        # Save individual event RFs.
        try:
            obspy.Stream(rfs).write(str(C.RF_DIR / f"{code}_event_rfs.h5"),
                                    format="H5")
        except Exception:
            pass
        rows.append(dict(code=code, lat=s["lat"], lon=s["lon"], kind=s["kind"],
                         n_rf=len(rfs), mean_rayp_skm=round(float(np.mean(rayps)), 4),
                         baz_list="|".join(f"{m[1]:.0f}" for m in meta)))
        if demo is None and s["kind"] == "SAM" and len(rfs) >= 4:
            demo = code   # auto-pick a good broadband station for the demo figure

    df = pd.DataFrame(rows).sort_values("n_rf", ascending=False)
    df.to_csv(C.DATA_PROCESSED / "rf_summary.csv", index=False)
    print(f"Computed RFs for {len(df)} stations "
          f"(median {int(df.n_rf.median())} RF/station, max {int(df.n_rf.max())})")
    print("Top stations:\n", df.head(8).to_string(index=False))

    if demo and (C.RF_DIR / f"{demo}_event_rfs.h5").exists():
        _demo_plot(demo)


def _demo_plot(code):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from rf import read_rf
    st = read_rf(str(C.RF_DIR / f"{code}_event_rfs.h5"))
    import obspy
    stack = obspy.read(str(C.RF_DIR / f"{code}_rf.sac"))[0]
    dt = stack.stats.delta
    t = np.arange(len(stack.data)) * dt - TSHIFT
    fig, ax = plt.subplots(figsize=(7, 8))
    for i, tr in enumerate(st):
        d = tr.data / (np.max(np.abs(tr.data)) or 1)
        tt = np.arange(len(d)) * tr.stats.delta - TSHIFT
        ax.plot(tt, d + i + 1, "k", lw=0.7)
        ax.fill_between(tt, i + 1, d + i + 1, where=(d > 0), color="C3", alpha=.6)
    ds = stack.data / (np.max(np.abs(stack.data)) or 1)
    ax.plot(t, ds, "b", lw=1.5)
    ax.fill_between(t, 0, ds, where=(ds > 0), color="C0", alpha=.5)
    ax.set_title(f"Receiver functions — station {code} (blue = stack)")
    ax.set_xlabel("Time after P (s)"); ax.set_ylabel("Event # / stack")
    ax.set_xlim(-2, RF_LEN); ax.axvline(0, color="gray", lw=.6)
    out = C.FIGURES / f"rf_demo_{code}.png"
    fig.tight_layout(); fig.savefig(out, dpi=200)
    print("Wrote demo RF figure", out)


if __name__ == "__main__":
    main()
