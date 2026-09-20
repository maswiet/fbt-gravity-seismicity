"""
Digitized 1-D S-wave velocity models — Western Indonesia (Sundaland).

Reads the digitized "Model Akhir" Vs profiles for 91 broadband stations across
Sumatra, Java, Kalimantan and Bali (from Downloads/digitized_velocity_models_
all_stations.xlsx) and produces publication-quality figures in the same PyGMT
house style as the Central Java RF+gravity study (GSHHG coastlines, fancy frame):

  figures/vs_westindo/map_moho_depth.png        Moho depth per station (map)
  figures/vs_westindo/map_sediment_thickness.png sediment thickness per station
  figures/vs_westindo/map_moho_grid.png         interpolated Moho depth surface
  figures/vs_westindo/vs_profiles_by_region.png  all Vs(z) grouped by island
  figures/vs_westindo/vs_slices_depth.png        Vs maps at 5/10/20/30 km depth
  figures/vs_westindo/relations.png             sediment/Moho stats & histograms

Run (fbt env):  python west_indonesia_vs/plot_vs_models.py
"""
from __future__ import annotations

import pathlib
import numpy as np
import pandas as pd

XLSX = pathlib.Path("/Users/maswiet/Downloads/digitized_velocity_models_all_stations.xlsx")
ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / "figures" / "vs_westindo"
FIG.mkdir(parents=True, exist_ok=True)

REGION = [95.0, 119.0, -9.5, 6.5]          # W, E, S, N — Sundaland
PROJ = "M17c"

# Island context (Holocene-scale reference points for the reader)
CITIES = [
    (98.68, 3.60, "Medan"), (100.37, -0.95, "Padang"),
    (104.75, -2.99, "Palembang"), (106.83, -6.21, "Jakarta"),
    (110.42, -6.97, "Semarang"), (112.75, -7.25, "Surabaya"),
    (117.15, -0.50, "Balikpapan"), (109.33, -0.03, "Pontianak"),
]


def region_of(lon, lat):
    """Coarse geographic grouping by island."""
    if lon < 107 and lat > -6.2:
        return "Sumatra"
    if lat <= -6.2 and lon < 116:
        return "Java-Bali"
    if lat > -4.5 and lon >= 107:
        return "Kalimantan"
    return "Java-Bali"


REGION_COLORS = {"Sumatra": "#B0512F", "Java-Bali": "#065A82",
                 "Kalimantan": "#02A676"}


def load():
    ss = pd.read_excel(XLSX, "Station_Summary")
    vd = pd.read_excel(XLSX, "Vs_Depth_1km")
    ss["region"] = [region_of(a, b) for a, b in zip(ss.longitude, ss.latitude)]
    reg = ss.set_index("station")["region"]
    vd["region"] = vd.station.map(reg)
    return ss, vd


# --------------------------------------------------------------------------
def _cfg(pygmt):
    pygmt.config(MAP_FRAME_TYPE="fancy+", MAP_FRAME_PEN="1.2p,gray15",
                 MAP_FRAME_WIDTH="0.14c", FONT_TITLE="17p,Helvetica-Bold",
                 FONT_ANNOT_PRIMARY="9p,Helvetica", FONT_LABEL="11p,Helvetica-Bold",
                 MAP_TICK_LENGTH_PRIMARY="0.12c",
                 MAP_GRID_PEN_PRIMARY="0.25p,gray70,.")


def _cities(fig, pygmt):
    cx = [c[0] for c in CITIES]; cy = [c[1] for c in CITIES]
    fig.plot(x=cx, y=cy, style="s0.20c", fill="white", pen="0.9p,black",
             region=REGION, projection=PROJ)
    for lon, lat, nm in CITIES:
        fig.text(x=lon, y=lat + 0.18, text=nm, font="8p,Helvetica-Bold,gray15",
                 justify="CB", fill="white@25", region=REGION, projection=PROJ)


def station_value_map(pygmt, ss, col, out, title, cbar, cmap, series, reverse=False):
    fig = pygmt.Figure(); _cfg(pygmt)
    fig.basemap(region=REGION, projection=PROJ,
                frame=["WSne+t" + title, "xa4f2", "ya2f1"])
    fig.coast(region=REGION, projection=PROJ, resolution="i",
              land="245/243/238", water="205/226/240",
              shorelines="1/0.4p,gray30", borders=["1/0.3p,gray55"])
    pygmt.makecpt(cmap=cmap, series=series, reverse=reverse)
    fig.plot(x=ss.longitude, y=ss.latitude, fill=ss[col], cmap=True,
             style="c0.30c", pen="0.5p,gray10")
    _cities(fig, pygmt)
    fig.colorbar(frame=["x+l" + cbar], position="JBC+o0c/0.9c+w10c/0.35c+h")
    fig.savefig(str(FIG / out), dpi=250)
    print("Wrote", out)


def moho_grid_map(pygmt, ss):
    import xarray as xr
    from scipy.interpolate import griddata
    lon = np.arange(REGION[0], REGION[1] + 1e-6, 0.1)
    lat = np.arange(REGION[2], REGION[3] + 1e-6, 0.1)
    LO, LA = np.meshgrid(lon, lat)
    z = griddata((ss.longitude, ss.latitude), ss.moho_depth_km, (LO, LA),
                 method="linear")
    da = xr.DataArray(z, coords={"lat": lat, "lon": lon}, dims=["lat", "lon"])
    fig = pygmt.Figure(); _cfg(pygmt)
    pygmt.makecpt(cmap="viridis", series=[16, 50, 2], reverse=True, background=True)
    fig.grdimage(grid=da, region=REGION, projection=PROJ, cmap=True,
                 nan_transparent=True,
                 frame=["WSne+tInterpolated Moho depth — Western Indonesia",
                        "xa4f2", "ya2f1"])
    fig.coast(region=REGION, projection=PROJ, resolution="i",
              shorelines="1/0.5p,gray15", borders=["1/0.3p,gray45"])
    fig.plot(x=ss.longitude, y=ss.latitude, style="c0.12c", fill="black",
             pen="0.3p,white")
    _cities(fig, pygmt)
    fig.colorbar(frame=["x+lMoho depth", "y+lkm"],
                 position="JBC+o0c/0.9c+w10c/0.35c+h")
    fig.savefig(str(FIG / "map_moho_grid.png"), dpi=250)
    print("Wrote map_moho_grid.png")


def vs_slice_maps(pygmt, vd):
    """Vs interpolated at 5/10/20/30 km depth, masked to land, montaged 2x2."""
    import subprocess
    import xarray as xr
    from scipy.interpolate import griddata
    depths = [5.5, 10.5, 20.5, 30.5]
    labels = ["Vs at 5 km depth", "Vs at 10 km depth",
              "Vs at 20 km depth", "Vs at 30 km depth"]
    lon = np.arange(REGION[0], REGION[1] + 1e-6, 0.1)
    lat = np.arange(REGION[2], REGION[3] + 1e-6, 0.1)
    LO, LA = np.meshgrid(lon, lat)
    landmask = pygmt.grdlandmask(region=REGION, spacing=0.1, resolution="i")
    proj = "M9c"
    tmp = []
    for d, lab in zip(depths, labels):
        sl = vd[np.isclose(vd.depth_mid_km, d)]
        z = griddata((sl.longitude, sl.latitude), sl.vs_km_s, (LO, LA),
                     method="linear")
        da = xr.DataArray(z, coords={"lat": lat, "lon": lon}, dims=["lat", "lon"])
        da = da.where(landmask.data > 0.5)                    # keep land only
        fig = pygmt.Figure(); _cfg(pygmt)
        pygmt.makecpt(cmap="turbo", background=True,
                      series=[np.floor(np.nanpercentile(sl.vs_km_s, 5) * 10) / 10,
                              np.ceil(np.nanpercentile(sl.vs_km_s, 95) * 10) / 10,
                              0.1])
        fig.grdimage(grid=da, region=REGION, projection=proj, cmap=True,
                     nan_transparent=True,
                     frame=["WSne+t" + lab, "xa4f2", "ya2f1"])
        fig.coast(region=REGION, projection=proj, resolution="i",
                  shorelines="1/0.4p,gray20", borders=["1/0.3p,gray55"])
        fig.plot(x=sl.longitude, y=sl.latitude, style="c0.10c",
                 fill="black", pen="0.2p,white", region=REGION, projection=proj)
        fig.colorbar(frame=["x+lVs (km/s)"],
                     position="JBC+o0c/0.9c+w7c/0.3c+h")
        p = FIG / f"_slice_{int(d)}.png"
        fig.savefig(str(p), dpi=200); tmp.append(str(p))
    out = str(FIG / "vs_slices_depth.png")
    subprocess.run(["/opt/homebrew/bin/magick", "montage", *tmp,
                    "-tile", "2x2", "-geometry", "+8+8", "-background", "white",
                    out], check=True)
    for p in tmp:
        pathlib.Path(p).unlink(missing_ok=True)
    print("Wrote vs_slices_depth.png")


# --------------------------------------------------------------------------
def vs_profiles(ss, vd):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    regions = ["Sumatra", "Java-Bali", "Kalimantan"]
    fig, axes = plt.subplots(1, 4, figsize=(15, 6.6), sharey=True,
                             gridspec_kw=dict(width_ratios=[1, 1, 1, 1.05]))
    for ax, rg in zip(axes[:3], regions):
        sub = vd[vd.region == rg]
        for st, g in sub.groupby("station"):
            g = g.sort_values("depth_mid_km")
            ax.plot(g.vs_km_s, g.depth_mid_km, color=REGION_COLORS[rg],
                    lw=0.7, alpha=0.28)
        # mean +/- std on a common depth axis
        piv = sub.pivot_table(index="depth_mid_km", columns="station",
                              values="vs_km_s")
        m = piv.mean(axis=1); sd = piv.std(axis=1)
        ax.plot(m, m.index, color="black", lw=2.4, label="mean")
        ax.fill_betweenx(m.index, m - sd, m + sd, color=REGION_COLORS[rg],
                         alpha=0.30, lw=0)
        n = sub.station.nunique()
        ax.set_title(f"{rg}  (n={n})", color=REGION_COLORS[rg], fontweight="bold")
        ax.set_xlabel("Vs (km/s)"); ax.grid(alpha=.3)
        ax.set_xlim(0, 5); ax.legend(loc="lower left", fontsize=8)
    axes[0].set_ylabel("Depth (km)")
    # 4th panel: regional mean profiles overlaid
    ax = axes[3]
    for rg in regions:
        sub = vd[vd.region == rg]
        piv = sub.pivot_table(index="depth_mid_km", columns="station",
                              values="vs_km_s")
        m = piv.mean(axis=1)
        ax.plot(m, m.index, color=REGION_COLORS[rg], lw=2.6, label=rg)
    ax.set_title("Regional mean Vs(z)", fontweight="bold")
    ax.set_xlabel("Vs (km/s)"); ax.set_xlim(0, 5); ax.grid(alpha=.3)
    ax.legend(loc="lower left", fontsize=9)
    axes[0].set_ylim(58, 0)
    fig.suptitle("Digitized 1-D S-wave velocity models — Western Indonesia "
                 f"({ss.station.nunique()} stations)", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(FIG / "vs_profiles_by_region.png", dpi=200)
    print("Wrote vs_profiles_by_region.png")


def relations(ss):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 2, figsize=(11, 8.5))
    # (a) sediment thickness histogram
    ax[0, 0].hist(ss.sediment_thickness_km, bins=np.arange(0, 11, 1),
                  color="#C98A1A", edgecolor="white")
    ax[0, 0].set_xlabel("Sediment thickness (km)"); ax[0, 0].set_ylabel("stations")
    ax[0, 0].set_title("(a) Sediment thickness", fontweight="bold")
    # (b) Moho depth histogram
    ax[0, 1].hist(ss.moho_depth_km, bins=np.arange(14, 54, 4),
                  color="#065A82", edgecolor="white")
    ax[0, 1].set_xlabel("Moho depth (km)"); ax[0, 1].set_ylabel("stations")
    ax[0, 1].set_title("(b) Moho depth", fontweight="bold")
    # (c) Moho depth vs longitude, colored by region
    for rg, c in REGION_COLORS.items():
        s = ss[ss.region == rg]
        ax[1, 0].scatter(s.longitude, s.moho_depth_km, c=c, label=rg, s=34,
                         edgecolor="white", lw=.5)
    ax[1, 0].set_xlabel("Longitude (deg)"); ax[1, 0].set_ylabel("Moho depth (km)")
    ax[1, 0].invert_yaxis(); ax[1, 0].set_title("(c) Crustal thickness trend",
                                                fontweight="bold")
    ax[1, 0].legend(fontsize=8); ax[1, 0].grid(alpha=.3)
    # (d) sediment thickness vs Moho depth
    sc = ax[1, 1].scatter(ss.sediment_thickness_km, ss.moho_depth_km,
                          c=ss.latitude, cmap="coolwarm", s=34,
                          edgecolor="white", lw=.5)
    ax[1, 1].set_xlabel("Sediment thickness (km)")
    ax[1, 1].set_ylabel("Moho depth (km)")
    ax[1, 1].set_title("(d) Sediment vs Moho", fontweight="bold")
    ax[1, 1].grid(alpha=.3)
    fig.colorbar(sc, ax=ax[1, 1], label="Latitude (deg)")
    fig.suptitle("Western Indonesia crustal structure — summary statistics",
                 fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(FIG / "relations.png", dpi=200)
    print("Wrote relations.png")


def main():
    ss, vd = load()
    print(f"Loaded {ss.station.nunique()} stations; "
          f"regions: {ss.region.value_counts().to_dict()}")
    # matplotlib figures
    vs_profiles(ss, vd)
    relations(ss)
    # PyGMT maps
    import pygmt
    station_value_map(pygmt, ss, "moho_depth_km", "map_moho_depth.png",
                      "Moho depth from digitized Vs models — Western Indonesia",
                      "Moho depth (km)", "viridis", [16, 50, 2], reverse=True)
    station_value_map(pygmt, ss, "sediment_thickness_km",
                      "map_sediment_thickness.png",
                      "Sediment thickness from Vs models — Western Indonesia",
                      "Sediment thickness (km)", "turbo", [0, 10, 1])
    moho_grid_map(pygmt, ss)
    vs_slice_maps(pygmt, vd)


if __name__ == "__main__":
    main()
