"""
RF-INDEPENDENT basement-depth MAP of Central Java from ambient-noise
autocorrelation (Romero & Schimmel 2018, Fig 8 style).

Processes every Central Java MERAMEX station through the multi-band PCC
autocorrelation + sidelobe discrimination (see multiband_basement.py), picks the
basement two-way time purely from the correlations (band-stable strongest negative
reflector), converts to depth with an independent sediment Vp, and draws a
filled-contour basement map in the R&S Fig-8 style (discrete depth CPT, GSHHG
coastline, station triangles, fancy frame, Times font).

Run (fbt):  python ambient_noise/basement_map.py --max-days 25            # process + map
            python ambient_noise/basement_map.py --map-only               # just redraw map
"""
from __future__ import annotations
import sys, os, argparse, pathlib
import numpy as np, pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ambient_noise"))
import multiband_basement as MB          # reuse process_day / band_stable_troughs / bands
from scipy.signal import hilbert

MER = pathlib.Path("/Volumes/Untitled/MERAMEX DATA")
INFO = MER / "DOY 260_1905" / "INFO.DAT"
INDEX = ROOT / "ambient_noise" / "pri0_index.txt"
FIG = ROOT / "figures" / "ambient_noise"
DATA = ROOT / "data" / "processed" / "rf_java"
OUTCSV = DATA / "basement_map_an.csv"
REGION = [109.4, 111.6, -8.2, -6.3]
VP, VP_LO, VP_HI = 3.0, 2.5, 3.5


def station_table():
    """code -> (lat, lon, [serials]) for all Central Java land stations."""
    tab = {}
    for ln in INFO.read_text(errors="ignore").splitlines():
        p = ln.split()
        if len(p) > 9 and p[1] in ("EDL", "SAM"):
            code, serial = p[7], p[0]
            try:
                lat, lon = float(p[8]), float(p[9])
            except ValueError:
                continue
            if REGION[0] <= lon <= REGION[1] and REGION[2] <= lat <= REGION[3]:
                d = tab.setdefault(code, [lat, lon, []])
                if serial not in d[2]:
                    d[2].append(serial)
    return tab


def pick_station(code, serials, allpaths, max_days):
    days = MB.days_for(serials, allpaths)
    if not days:
        return None
    dl = sorted(days)[:max_days]
    nlag, nwin = int(MB.MAXLAG * MB.FS_EFF), int(MB.WIN * MB.FS_EFF)
    acc = [MB.process_day(code, dy, days[dy], nlag, nwin) for dy in dl]
    A = np.array(acc)
    if A.size == 0:
        return None
    lag = np.arange(nlag + 1) / MB.FS_EFF
    stacks, cohs = [], []
    for bi in range(len(MB.BANDS)):
        M = A[:, bi, :]
        coh = np.abs(np.exp(1j * np.angle(hilbert(M, axis=1))).mean(0))
        stacks.append(M.mean(0) * coh ** 2); cohs.append(coh)
    stacks = np.array(stacks); cohs = np.array(cohs)
    stable = MB.band_stable_troughs(lag, stacks)
    if not stable:
        return None
    strength = []
    for t in stable:
        k = int(round(t * MB.FS_EFF))
        strength.append(np.mean([abs(stacks[bi][k] * cohs[bi][k]) for bi in range(len(MB.BANDS))]))
    tb = stable[int(np.argmax(strength))]
    return tb, tb * VP / 2, len(dl)


def process(max_days):
    allpaths = INDEX.read_text().splitlines()
    tab = station_table()
    print(f"Central Java land stations: {len(tab)}")
    rows = []
    for i, (code, (lat, lon, serials)) in enumerate(sorted(tab.items())):
        try:
            r = pick_station(code, serials, allpaths, max_days)
        except Exception as e:
            print(f"  {code}: err {type(e).__name__}"); r = None
        if r:
            tb, depth, nd = r
            rows.append(dict(code=code, lon=lon, lat=lat, twt=round(tb, 2),
                             depth_km=round(depth, 2), ndays=nd))
        if (i + 1) % 10 == 0:
            print(f"  ...{i+1}/{len(tab)} stations, {len(rows)} picked")
    df = pd.DataFrame(rows)
    df.to_csv(OUTCSV, index=False)
    print(f"Wrote {OUTCSV}: {len(df)} basement picks")
    return df


def draw_map(df):
    import pygmt
    proj = "M16c"
    pygmt.config(FONT="12p,Times-Roman", FONT_TITLE="16p,Times-Bold",
                 MAP_FRAME_TYPE="fancy+", MAP_FRAME_PEN="1.4p,black",
                 MAP_FRAME_WIDTH="0.18c", FONT_ANNOT_PRIMARY="10p,Times-Roman")
    fig = pygmt.Figure()
    # interpolate basement depth (km) to a grid, minimum curvature
    grd = pygmt.surface(x=df.lon, y=df.lat, z=df.depth_km, spacing=0.03,
                        region=REGION, tension=0.35)
    series = "0/6.5/0.5"
    pygmt.makecpt(cmap="turbo", series=series, reverse=True, continuous=False)
    fig.basemap(region=REGION, projection=proj,
                frame=["WSne+tCentral Java basement depth from ambient-noise autocorrelation",
                       "xa0.5f0.25", "ya0.5f0.25"])
    fig.grdimage(grid=grd, cmap=True, nan_transparent=True, region=REGION, projection=proj)
    fig.coast(region=REGION, projection=proj, resolution="f",
              shorelines="1/0.6p,black", borders=["1/0.3p,gray40"], water="white@60")
    fig.plot(x=df.lon, y=df.lat, style="t0.34c", fill="red2", pen="0.6p,black",
             region=REGION, projection=proj)
    fig.colorbar(frame=["x+lBasement depth", "y+lkm"],
                 position="JBC+o0c/0.9c+w9c/0.4c+h")
    # inset (Java) top-right
    with fig.inset(position="jTR+w3.6c+o0.2c", box="+p1p,black"):
        fig.coast(region=[105, 116, -9, -5], projection="M3.6c", land="gray85",
                  water="white", shorelines="1/0.3p", frame="+gwhite")
        fig.plot(x=[REGION[0], REGION[1], REGION[1], REGION[0], REGION[0]],
                 y=[REGION[2], REGION[2], REGION[3], REGION[3], REGION[2]],
                 pen="1.2p,red", projection="M3.6c", region=[105, 116, -9, -5])
    fig.savefig(str(FIG / "basement_map_an.png"), dpi=250)
    print("Wrote basement_map_an.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-days", type=int, default=25)
    ap.add_argument("--map-only", action="store_true")
    a = ap.parse_args()
    if a.map_only:
        df = pd.read_csv(OUTCSV)
    else:
        df = process(a.max_days)
    print(f"Basement picks: n={len(df)}, depth {df.depth_km.min():.1f}-{df.depth_km.max():.1f} km, "
          f"median {df.depth_km.median():.1f} km")
    draw_map(df)


if __name__ == "__main__":
    main()
