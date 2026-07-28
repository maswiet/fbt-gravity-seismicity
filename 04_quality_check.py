"""
04_quality_check.py

Sanity check dan QC plots setelah pra-pemrosesan.

Generate:
- Peta FAA, CBA, residual, derivatives
- Peta seismisitas crustal vs density
- Cross-section gabungan
- Statistik output (range, mean, std, NaN count)
"""
import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import pygmt

DATA_OUT = Path("data/processed")
FIG = Path("figures")
FIG.mkdir(exist_ok=True)


def stat_report(da: xr.DataArray):
    print(f"  {da.name:25s}: "
          f"min={float(da.min()):8.2f} max={float(da.max()):8.2f} "
          f"mean={float(da.mean()):8.2f} std={float(da.std()):8.2f} "
          f"NaN={int(da.isnull().sum())}")


def plot_grid_pygmt(da, title, cmap, region, outfile, units="mGal"):
    fig = pygmt.Figure()
    fig.basemap(region=region, projection="M15c", frame=["af", f'+t"{title}"'])
    fig.grdimage(grid=da, cmap=cmap, shading="+a45+nt0.5", region=region)
    fig.coast(shorelines="0.3p,black", resolution="h")
    fig.colorbar(frame=f'af+l"{units}"')
    # Tambahkan kontur untuk bantu interpretasi
    fig.grdcontour(grid=da, interval=20, annotation=40, pen="0.2p,gray30")
    fig.savefig(outfile, dpi=300)
    print(f"  → Saved {outfile}")


def main():
    print("=== QC Gravitasi ===")
    for name in ["faa_merged", "sba", "cba", "cba_residual", "cba_regional"]:
        try:
            da = xr.open_dataarray(DATA_OUT / f"{name}.nc")
            stat_report(da)
        except FileNotFoundError:
            print(f"  ! {name}.nc tidak ada — skip")

    print("\n=== QC Derivatives ===")
    for name in ["thdr", "tdr", "tdx"]:
        try:
            da = xr.open_dataarray(DATA_OUT / "derivatives" / f"{name}.nc")
            stat_report(da)
        except FileNotFoundError:
            pass

    print("\n=== QC Seismisitas ===")
    for f in ["catalog_crustal.csv", "catalog_crustal_declustered.csv",
              "catalog_thrust.csv"]:
        path = DATA_OUT / f
        if path.exists():
            df = pd.read_csv(path)
            print(f"  {f:40s}: {len(df):6d} events, "
                  f"depth {df.depth.min():.1f}-{df.depth.max():.1f} km, "
                  f"M {df.mag.min() if 'mag' in df else df.mw.min():.1f}-"
                  f"{df.mag.max() if 'mag' in df else df.mw.max():.1f}")

    # Generate peta-peta utama
    print("\n=== Generating maps ===")
    region = [114, 124, -11, -7]

    # CBA
    cba = xr.open_dataarray(DATA_OUT / "cba.nc")
    plot_grid_pygmt(cba, "Complete Bouguer Anomaly", "polar+h0", region,
                    FIG / "map_cba.png", "mGal")

    # Residual
    res = xr.open_dataarray(DATA_OUT / "cba_residual.nc")
    plot_grid_pygmt(res, "Residual CBA (high-pass)", "polar+h0", region,
                    FIG / "map_cba_residual.png", "mGal")

    # THDR overlay seismisitas
    thdr = xr.open_dataarray(DATA_OUT / "derivatives" / "thdr.nc")
    decl = pd.read_csv(DATA_OUT / "catalog_crustal_declustered.csv")

    fig = pygmt.Figure()
    fig.basemap(region=region, projection="M15c",
                frame=["af", '+t"THDR + Crustal Seismicity"'])
    fig.grdimage(grid=thdr, cmap="hot", region=region)
    fig.coast(shorelines="0.3p,black", resolution="h")
    fig.plot(x=decl.lon, y=decl.lat, style="c0.08c",
             fill="white", pen="0.2p,black")
    fig.colorbar(frame='af+l"THDR (mGal/m)"')
    fig.savefig(FIG / "map_thdr_seismicity.png", dpi=300)
    print(f"  → {FIG}/map_thdr_seismicity.png")

    print("\n✓ QC selesai. Periksa folder figures/.")


if __name__ == "__main__":
    main()
