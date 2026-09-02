"""
Parse the MERAMEX INFO.DAT network-metadata file into a clean station table.

INFO.DAT line (EDL/SAM land + OBH/OBS marine):
  <serial> <TYPE> <ver> <fmt> <sensor> <sensorSN> <idx> <STA> <lat> <lon>
  <elev_m> <startdate> <starttime> <enddate> <endtime> <operator>

Station codes can repeat (site re-occupied / instrument swapped) with consistent
coordinates; we deduplicate by code. Output: stations.csv (code, lat, lon,
elev_m, kind, sensor, serials).

Run:  python rf_gravity_java/parse_stations.py
"""
from __future__ import annotations

import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C

# code (2-3 alnum) lat lon elev  then a YYYY.MM.DD date
ROW = re.compile(
    r"^\s*(\d{3,4})\s+(EDL|SAM|OBH|OBS)\s+.*?\s([A-Z0-9]{2,3})\s+"
    r"(-?\d+\.\d+)\s+(-?\d+\.\d+)\s+(-?\d+)\s+\d{4}\.\d{2}\.\d{2}"
)


def main():
    import pandas as pd
    C.ensure_dirs()
    rows = []
    for line in C.MERAMEX_INFO.read_text(errors="replace").splitlines():
        if line.lstrip().startswith("#") or not line.strip():
            continue
        m = ROW.match(line)
        if not m:
            continue
        serial, kind, code, lat, lon, elev = m.groups()
        # sensor = token 5 (0-based 4) in the whitespace split
        toks = line.split()
        sensor = toks[4] if len(toks) > 4 else ""
        rows.append(dict(code=code.upper(), kind=kind, lat=float(lat),
                         lon=float(lon), elev_m=float(elev), sensor=sensor,
                         serial=serial))
    df = pd.DataFrame(rows)
    if df.empty:
        raise SystemExit("No rows parsed — check INFO.DAT format/regex.")

    # Deduplicate by station code (keep first coord; collect serials/sensors).
    agg = (df.groupby("code")
             .agg(lat=("lat", "first"), lon=("lon", "first"),
                  elev_m=("elev_m", "first"), kind=("kind", "first"),
                  sensor=("sensor", lambda s: "/".join(sorted(set(s)))),
                  serials=("serial", lambda s: "/".join(sorted(set(s)))),
                  n=("serial", "size"))
             .reset_index())
    agg = agg.sort_values("code").reset_index(drop=True)
    agg.to_csv(C.STATIONS_CSV, index=False)

    land = agg[agg.kind.isin(["EDL", "SAM"])]
    sea = agg[agg.kind.isin(["OBH", "OBS"])]
    print(f"Parsed {len(df)} rows -> {len(agg)} unique station codes "
          f"({len(land)} land, {len(sea)} marine)")
    print(f"  land lon [{land.lon.min():.3f},{land.lon.max():.3f}] "
          f"lat [{land.lat.min():.3f},{land.lat.max():.3f}]")
    print(f"  broadband (SAM): {sorted(agg[agg.kind=='SAM'].code.tolist())}")
    print("Wrote", C.STATIONS_CSV)


if __name__ == "__main__":
    main()
