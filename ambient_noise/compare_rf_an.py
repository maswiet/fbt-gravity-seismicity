"""
Two seismological routes to the Central Java basin, side by side, in the
Romero & Schimmel Fig-8 style:
  (a) Receiver functions  — sediment thickness from Ps move-out
  (b) Ambient-noise autocorrelation (Romero & Schimmel 2018) — RF-independent
Both drawn with identical PyGMT styling, then montaged.

Run (fbt):  python ambient_noise/compare_rf_an.py
"""
from __future__ import annotations
import subprocess, pathlib
import pandas as pd, pygmt

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / "figures" / "ambient_noise"
DATA = ROOT / "data" / "processed" / "rf_java"
REGION = [109.4, 111.6, -8.2, -6.3]


def draw(df, title, out):
    pygmt.config(FONT="12p,Times-Roman", FONT_TITLE="15p,Times-Bold",
                 MAP_FRAME_TYPE="fancy+", MAP_FRAME_PEN="1.4p,black",
                 MAP_FRAME_WIDTH="0.16c", FONT_ANNOT_PRIMARY="10p,Times-Roman")
    fig = pygmt.Figure()
    d = df.copy(); d["z"] = d.z.clip(0.5, 6.0)
    bm = pygmt.blockmedian(x=d.lon, y=d.lat, z=d.z, spacing=0.05, region=REGION)
    grd = pygmt.surface(data=bm, spacing=0.02, region=REGION, tension=0.4)
    pygmt.makecpt(cmap="turbo", series="0/6/0.5", reverse=True, continuous=False)
    fig.basemap(region=REGION, projection="M14c",
                frame=["WSne+t" + title, "xa0.5f0.25", "ya0.5f0.25"])
    fig.grdimage(grid=grd, cmap=True, nan_transparent=True, region=REGION, projection="M14c")
    fig.coast(region=REGION, projection="M14c", resolution="f",
              shorelines="1/0.6p,black", borders=["1/0.3p,gray40"], water="white@55")
    fig.plot(x=df.lon, y=df.lat, style="t0.30c", fill="red2", pen="0.6p,black",
             region=REGION, projection="M14c")
    fig.colorbar(frame=["x+lBasement depth", "y+lkm"], position="JBC+o0c/0.9c+w8c/0.35c+h")
    fig.savefig(str(out), dpi=230)
    print("Wrote", out.name)


def main():
    rf = pd.read_csv(DATA / "sediment_rf.csv")
    rf = rf[rf.kind.isin(["EDL", "SAM"]) & (rf.h_sed_km > 0)][["lon", "lat", "h_sed_km"]].rename(
        columns={"h_sed_km": "z"})
    an = pd.read_csv(DATA / "basement_map_an.csv")[["lon", "lat", "depth_km"]].rename(
        columns={"depth_km": "z"})
    p_rf = FIG / "_cmp_rf.png"; p_an = FIG / "_cmp_an.png"
    draw(rf, "(a) Receiver functions (Ps move-out)", p_rf)
    draw(an, "(b) Ambient-noise autocorrelation (Romero & Schimmel)", p_an)
    out = FIG / "basement_two_approaches.png"
    subprocess.run(["/opt/homebrew/bin/magick", "montage", str(p_rf), str(p_an),
                    "-tile", "2x1", "-geometry", "+10+10", "-background", "white", str(out)],
                   check=True)
    p_rf.unlink(missing_ok=True); p_an.unlink(missing_ok=True)
    print("Wrote", out)


if __name__ == "__main__":
    main()
