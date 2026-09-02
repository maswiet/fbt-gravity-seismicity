"""
Identify the teleseismic events behind the ARTHA event windows.

Each ARTHA file (aa#c_DOY, GCF) is a ~30-min window cut around a teleseismic P
arrival in 2004. We read one window start time per DOY, then match it to the
global USGS catalog (M>=MAG_MIN) by requiring a theoretical P arrival (iasp91)
at the network centre to fall inside the window and 30<=dist<=95 deg.

Output: events.csv (doy, win_start, origin_time, evlat, evlon, evdepth_km, mag,
dist_deg_center, baz_center). Needs network access (obspy FDSN + TauP).

Run:  python rf_gravity_java/build_events.py
"""
from __future__ import annotations

import glob
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C


def window_starts_by_doy():
    """One representative Z-window start UTCDateTime per DOY from ARTHA."""
    import obspy
    doys = {}
    for f in glob.glob(str(C.ARTHA_DIR / "*z_*")):
        m = re.search(r"z_(\d+)$", f)
        if not m:
            continue
        doy = int(m.group(1))
        if doy in doys:
            continue
        try:
            st = obspy.read(f, headonly=True)
            doys[doy] = obspy.UTCDateTime(st[0].stats.starttime)
        except Exception:
            pass
    return dict(sorted(doys.items()))


def main():
    import numpy as np
    import pandas as pd
    from obspy.clients.fdsn import Client
    from obspy.geodetics import locations2degrees, gps2dist_azimuth
    from obspy.taup import TauPyModel

    C.ensure_dirs()
    sta = pd.read_csv(C.STATIONS_CSV)
    land = sta[sta.kind.isin(["EDL", "SAM"])]
    clat, clon = land.lat.mean(), land.lon.mean()
    print(f"Network centre: {clat:.3f}, {clon:.3f}")

    starts = window_starts_by_doy()
    print("DOY window starts:", {d: str(t) for d, t in starts.items()})

    t0 = min(starts.values()) - 3600
    t1 = max(starts.values()) + 3600
    client = Client("USGS")
    cat = client.get_events(starttime=t0 - 2400, endtime=t1,
                            minmagnitude=C.MAG_MIN)
    print(f"Catalog: {len(cat)} events M>={C.MAG_MIN} in window")
    model = TauPyModel(model="iasp91")

    rows = []
    for doy, wstart in starts.items():
        cands = []
        for ev in cat:
            o = ev.preferred_origin() or ev.origins[0]
            mag = (ev.preferred_magnitude() or ev.magnitudes[0]).mag
            dist = locations2degrees(clat, clon, o.latitude, o.longitude)
            if not (C.DIST_MIN <= dist <= C.DIST_MAX):
                continue
            try:
                arr = model.get_travel_times(source_depth_in_km=max(o.depth/1000, 0),
                                             distance_in_degree=dist,
                                             phase_list=["P", "Pdiff"])
            except Exception:
                continue
            if not arr:
                continue
            p_arr = o.time + arr[0].time
            # P must land within the 30-min window (generous pre/post-roll).
            if wstart - 300 <= p_arr <= wstart + 1900:
                cands.append((mag, o, dist, p_arr))
        if not cands:
            print(f"  DOY {doy}: NO catalog match (0 cand)"); continue
        # Prefer the largest-magnitude in-window teleseism.
        cands.sort(key=lambda x: -x[0])
        mag, o, dist, p_arr = cands[0]
        _, az, baz = gps2dist_azimuth(clat, clon, o.latitude, o.longitude)
        if len(cands) > 1:
            print(f"  DOY {doy}: {len(cands)} candidates, picked M{mag:.1f}")
        rows.append(dict(doy=doy, win_start=str(wstart), origin_time=str(o.time),
                         evlat=o.latitude, evlon=o.longitude,
                         evdepth_km=o.depth/1000.0, mag=mag,
                         dist_deg_center=round(dist, 2), baz_center=round(baz, 1)))
        print(f"  DOY {doy}: {o.time} M{mag:.1f} d={dist:.1f}deg baz={baz:.0f} "
              f"({o.latitude:.2f},{o.longitude:.2f})")

    df = pd.DataFrame(rows)
    out = C.DATA_PROCESSED / "events.csv"
    df.to_csv(out, index=False)
    print(f"Matched {len(df)}/{len(starts)} events -> {out}")


if __name__ == "__main__":
    main()
