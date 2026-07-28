"""
16 — Final inversion, maps, and validation figures.

With the hyperparameters from step 15, run the final inversion and produce the
paper-equivalent figures:
  - Estimated Moho depth map (Fig. 11)
  - Gravity residuals map + histogram (Fig. 12a)
  - Difference between estimated and seismic Moho, map + histogram (Fig. 12b)

Plotting uses matplotlib + cartopy (no GMT binary needed). The plotting functions
take plain arrays, so they can be previewed with synthetic data via `--demo`
before the real pipeline has been run.

Run:
    python moho_indonesia/16_results_maps.py --demo   # preview figures (no data)
    python moho_indonesia/16_results_maps.py          # real run (needs 10-15 done)
"""
from __future__ import annotations

import argparse
import json

import numpy as np

from _bootstrap import C, mu


# --------------------------------------------------------------------------
# Map helpers (cartopy, with offline-safe coastlines)
# --------------------------------------------------------------------------
def _make_ax(fig, position, extent, title):
    import cartopy.crs as ccrs
    ax = fig.add_subplot(position, projection=ccrs.PlateCarree())
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    try:                                   # Natural Earth needs a one-off download
        ax.coastlines(resolution="110m", linewidth=0.6)
    except Exception:
        pass
    gl = ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.5)
    gl.top_labels = gl.right_labels = False
    ax.set_title(title)
    return ax


# Approximate tectonic context lines (lon, lat), for orientation only — NOT
# authoritative geometry. Replace with Bird (2003) / official traces for figures.
def _tectonic_features():
    sunda_banda_trench = [
        (92.5, 6.0), (93.5, 3.5), (95.0, 1.0), (97.0, -1.5), (99.0, -3.5),
        (101.0, -5.2), (103.5, -6.6), (106.5, -8.0), (110.0, -9.2),
        (113.0, -10.2), (116.0, -10.8), (119.0, -10.9), (121.5, -10.4),
        (123.5, -9.2), (125.0, -7.8), (126.5, -6.8), (128.0, -6.5),
    ]
    sumatran_fault = [
        (95.5, 5.3), (97.0, 4.0), (98.5, 2.4), (99.6, 0.9), (100.6, -0.6),
        (101.6, -2.1), (102.6, -3.6), (103.6, -5.0), (104.3, -5.9),
    ]
    return {"Sunda–Banda trench (approx.)": (sunda_banda_trench, dict(color="k", lw=1.6, ls="-")),
            "Sumatran Fault (approx.)": (sumatran_fault, dict(color="red", lw=1.4, ls="-"))}


def _add_tectonics(ax):
    import cartopy.crs as ccrs
    for label, (pts, style) in _tectonic_features().items():
        arr = np.array(pts)
        ax.plot(arr[:, 0], arr[:, 1], transform=ccrs.PlateCarree(),
                label=label, **style)


def _add_moho_contours(ax, lon, lat, moho_km):
    import cartopy.crs as ccrs
    levels = np.arange(15, 55, 5)
    cs = ax.contour(lon, lat, moho_km, levels=levels, colors="k",
                    linewidths=0.4, alpha=0.6, transform=ccrs.PlateCarree())
    ax.clabel(cs, fmt="%d", fontsize=6, inline=True)
    ax.contour(lon, lat, moho_km, levels=[35], colors="white", linewidths=1.4,
               transform=ccrs.PlateCarree())


def plot_moho_map(moho_km, lon, lat, seismic_df=None, out=None,
                  title="Estimated Moho depth (km)",
                  contours=True, tectonics=True):
    import cartopy.crs as ccrs
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(9, 5))
    ax = _make_ax(fig, 111, C.REGION, title)
    pcm = ax.pcolormesh(lon, lat, moho_km, cmap="viridis", shading="auto",
                        transform=ccrs.PlateCarree())
    fig.colorbar(pcm, ax=ax, shrink=0.8, label="Moho depth (km)")
    if contours:
        _add_moho_contours(ax, lon, lat, moho_km)
    if tectonics:
        _add_tectonics(ax)
    if seismic_df is not None:
        ax.scatter(seismic_df.longitude, seismic_df.latitude, c=seismic_df.depth_km,
                   cmap="viridis", edgecolor="k", linewidth=0.4, s=28,
                   transform=ccrs.PlateCarree(), label="seismic Moho")
    ax.legend(loc="lower left", fontsize=7, framealpha=0.9)
    fig.tight_layout()
    if out:
        fig.savefig(out, dpi=150)
        print("Wrote", out)
    return fig


def plot_gravity_residual(residual, lon, lat, out=None):
    import cartopy.crs as ccrs
    import matplotlib.pyplot as plt

    vmax = float(np.nanpercentile(np.abs(residual), 98))
    fig = plt.figure(figsize=(12, 4.6))
    ax = _make_ax(fig, 121, C.REGION, "Gravity residuals (mGal)")
    pcm = ax.pcolormesh(lon, lat, residual, cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                        shading="auto", transform=ccrs.PlateCarree())
    fig.colorbar(pcm, ax=ax, shrink=0.8, label="mGal")
    ax2 = fig.add_subplot(122)
    ax2.hist(residual.ravel(), bins=40, color="steelblue")
    ax2.set(xlabel="residual (mGal)", ylabel="count",
            title=f"mean={np.nanmean(residual):.2f}, std={np.nanstd(residual):.2f}")
    fig.tight_layout()
    if out:
        fig.savefig(out, dpi=150)
        print("Wrote", out)
    return fig


def plot_difference_from_seismic(moho_km, lon, lat, seismic_df, out=None):
    import cartopy.crs as ccrs
    import matplotlib.pyplot as plt
    from scipy.interpolate import RegularGridInterpolator

    interp = RegularGridInterpolator((lat[:, 0], lon[0, :]), moho_km,
                                     bounds_error=False, fill_value=np.nan)
    estimated = interp(np.column_stack([seismic_df.latitude, seismic_df.longitude]))
    diff = estimated - seismic_df.depth_km.values
    ok = np.isfinite(diff)
    vmax = float(np.nanpercentile(np.abs(diff[ok]), 98)) if ok.any() else 10.0

    fig = plt.figure(figsize=(12, 4.6))
    ax = _make_ax(fig, 121, C.REGION, "Estimated − seismic Moho (km)")
    _add_tectonics(ax)
    sc = ax.scatter(seismic_df.longitude[ok], seismic_df.latitude[ok], c=diff[ok],
                    cmap="PuOr", vmin=-vmax, vmax=vmax, edgecolor="k", linewidth=0.4,
                    s=34, transform=ccrs.PlateCarree())
    fig.colorbar(sc, ax=ax, shrink=0.8, label="km")
    ax.legend(loc="lower left", fontsize=7, framealpha=0.9)
    ax2 = fig.add_subplot(122)
    ax2.hist(diff[ok], bins=25, color="peru")
    ax2.set(xlabel="estimated − seismic (km)", ylabel="count",
            title=f"mean={np.nanmean(diff[ok]):.2f}, std={np.nanstd(diff[ok]):.2f} km")
    fig.tight_layout()
    if out:
        fig.savefig(out, dpi=150)
        print("Wrote", out)
    return fig


# --------------------------------------------------------------------------
# Real run
# --------------------------------------------------------------------------
def final_inversion():
    """Run the inversion with the chosen hyperparameters; return (moho, residual, lon, lat)."""
    import importlib.util as ilu
    import pathlib as pl
    import sys as _sys
    spec = ilu.spec_from_file_location(
        "moho_inversion", pl.Path(__file__).with_name("14_moho_inversion.py"))
    moho_inversion = ilu.module_from_spec(spec)
    _sys.modules[spec.name] = moho_inversion      # register so @dataclass resolves
    spec.loader.exec_module(moho_inversion)

    hp = json.loads(C.HYPERPARAMS_JSON.read_text())
    observed = mu.load_grid(C.GRID_SED_FREE_BOUGUER)
    lon, lat = mu.make_grid_coordinates()
    result = moho_inversion.invert(observed.values, lon, lat, drho=hp["drho"],
                                   z_ref_km=hp["z_ref_km"], mu_reg=hp["mu"])
    mu.save_grid(result.moho_depth_km, lon, lat, C.GRID_MOHO,
                 name="moho_depth", attrs={"units": "km"})
    return (result.moho_depth_km, result.residual.reshape(observed.shape), lon, lat)


def main() -> None:
    C.ensure_dirs()
    moho, residual, lon, lat = final_inversion()
    seismic = mu.load_seismic_moho()
    plot_moho_map(moho, lon, lat, seismic, out=C.FIGURES / "moho_depth.png")
    plot_gravity_residual(residual, lon, lat, out=C.FIGURES / "gravity_residual.png")
    plot_difference_from_seismic(moho, lon, lat, seismic,
                                 out=C.FIGURES / "difference_from_seismic.png")
    print("Figures written to", C.FIGURES)


# --------------------------------------------------------------------------
# Preview / demo (synthetic Moho + real seismic points; no data/harmonica needed)
# --------------------------------------------------------------------------
def _demo_moho(lon, lat):
    """A plausible-looking SYNTHETIC Moho for previewing the figure design.

    Deep root (~40 km) along a Sumatra-Java-Banda arc line, shallow (~15 km)
    oceanic elsewhere. NOT a real result.
    """
    base = 18.0
    arc = 22.0 * np.exp(-((lat - (-2.0 - 0.15 * (lon - 100))) ** 2) / 6.0)
    craton = 8.0 * np.exp(-(((lon - 134) ** 2 + (lat + 4) ** 2) / 40.0))
    return base + arc + craton


def demo() -> None:
    C.ensure_dirs()
    w, e, s, n = C.REGION
    lon, lat = np.meshgrid(np.arange(w, e + C.SPACING, C.SPACING),
                           np.arange(s, n + C.SPACING, C.SPACING))
    moho = _demo_moho(lon, lat)
    rng = np.random.default_rng(0)
    residual = 6.0 * np.sin(lon / 4.0) * np.cos(lat / 3.0) + rng.normal(0, 2, lon.shape)
    seismic = mu.load_seismic_moho()

    plot_moho_map(moho, lon, lat, seismic,
                  out=C.FIGURES / "preview_moho_depth.png",
                  title="[DEMO] Estimated Moho depth (km) — synthetic + real seismic points")
    plot_gravity_residual(residual, lon, lat,
                          out=C.FIGURES / "preview_gravity_residual.png")
    plot_difference_from_seismic(moho, lon, lat, seismic,
                                 out=C.FIGURES / "preview_difference_from_seismic.png")
    print("Preview figures written to", C.FIGURES)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Moho results & figures.")
    parser.add_argument("--demo", action="store_true",
                        help="Render preview figures from synthetic Moho + real seismic points.")
    args = parser.parse_args()
    demo() if args.demo else main()
