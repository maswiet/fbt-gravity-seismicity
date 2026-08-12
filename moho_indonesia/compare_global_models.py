"""
compare_global_models — quantitative comparison of the gravity Moho against global
reference models (CRUST1.0, and GEMMA if available) at the 105 seismic points, plus
diagnostic figures (depth--depth scatter, validation-point map, residual maps).

Addresses the reviewers' top request. Run (fbt env):
    python moho_indonesia/compare_global_models.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
import cartopy.crs as ccrs               # noqa: E402
import cartopy.feature as cfeature       # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402


def crust1_moho_grid():
    """CRUST1.0 Moho depth (km, positive down) on its native 1-deg grid."""
    bnds = np.loadtxt(C.CRUST1_DIR / "crust1.bnds").reshape(180, 360, -1)
    moho = -bnds[:, :, 8]                 # boundary 8 = top of mantle (km, +up -> +down)
    clat = np.arange(89.5, -90.0, -1.0)
    clon = np.arange(-179.5, 180.0, 1.0)
    return clat, clon, moho


def sample(grid_interp, lon, lat):
    return grid_interp(np.column_stack([lat, lon]))


def stats(diff):
    d = diff[np.isfinite(diff)]
    return dict(N=d.size, mean=d.mean(), median=np.median(d), std=d.std(ddof=1),
                iqr=np.subtract(*np.percentile(d, [75, 25])),
                rms=np.sqrt(np.mean(d ** 2)),
                p5=100 * np.mean(np.abs(d) <= 5), p10=100 * np.mean(np.abs(d) <= 10))


def main():
    seis = mu.load_seismic_moho()
    slon, slat, sdep = seis.longitude.values, seis.latitude.values, seis.depth_km.values

    d = xr.open_dataarray(C.GRID_MOHO)
    ours_i = RegularGridInterpolator((d.latitude.values, d.longitude.values), d.values,
                                     bounds_error=False, fill_value=np.nan)
    ours = sample(ours_i, slon, slat)

    clat, clon, cmoho = crust1_moho_grid()
    crust_i = RegularGridInterpolator((clat[::-1], clon), cmoho[::-1, :],
                                      bounds_error=False, fill_value=np.nan)
    crust = sample(crust_i, slon, slat)

    models = {"This study (gravity)": ours, "CRUST1.0": crust}
    gpath = C.DATA_EXTERNAL / "gemma" / "gemma_moho.nc"
    if gpath.exists():
        g = xr.open_dataarray(gpath)
        gi = RegularGridInterpolator((g.latitude.values, g.longitude.values), g.values,
                                     bounds_error=False, fill_value=np.nan)
        models["GEMMA"] = sample(gi, slon, slat)

    header = (f"{'Model':22s} {'N':>3s} {'mean':>6s} {'med':>6s} {'std':>5s} "
              f"{'IQR':>5s} {'RMS':>5s} {'r':>5s} {'±5km':>6s} {'±10km':>6s}")
    print(header)
    rows = [header]
    corr = {}
    for name, est in models.items():
        diff = est - sdep
        ok = np.isfinite(diff)
        s = stats(diff)
        r = np.corrcoef(est[ok], sdep[ok])[0, 1]
        corr[name] = r
        line = (f"{name:22s} {s['N']:3d} {s['mean']:+6.2f} {s['median']:+6.2f} "
                f"{s['std']:5.2f} {s['iqr']:5.2f} {s['rms']:5.2f} {r:5.2f} "
                f"{s['p5']:5.0f}% {s['p10']:5.0f}%")
        print(line); rows.append(line)
    (C.FIGURES / "compare_global_models.txt").write_text("\n".join(rows) + "\n")

    palette = {"This study (gravity)": ("#c0392b", "o"),
               "CRUST1.0": ("#2f6db0", "s"), "GEMMA": ("#e08a1e", "^")}
    # ---- Fig: depth-depth scatter (all models vs seismic) + regression + bin means ----
    ours_ok = np.isfinite(ours)
    slope, intercept = np.polyfit(sdep[ours_ok], ours[ours_ok], 1)   # OLS: model on seismic
    print(f"This-study OLS fit: slope={slope:.2f}, intercept={intercept:.1f} km "
          f"(slope<1 => amplitude compression)")
    edges = np.array([20, 25, 30, 35, 41])
    bctr, bmean, bstd = [], [], []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (sdep >= a) & (sdep < b) & ours_ok
        if m.sum():
            bctr.append(sdep[m].mean()); bmean.append(ours[m].mean()); bstd.append(ours[m].std())

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot([5, 60], [5, 60], "k--", lw=1, zorder=0, label="1:1")
    for name, est in models.items():
        c, m = palette.get(name, ("gray", "o"))
        ax.scatter(sdep, est, s=26, c=c, edgecolor="k", lw=0.25, marker=m, alpha=0.55,
                   label=f"{name.replace(' (gravity)','')} (r={corr[name]:.2f})")
    xr_ = np.array([18, 42])
    ax.plot(xr_, slope * xr_ + intercept, "-", color="#7a0f0f", lw=2.2, zorder=5,
            label=f"This-study fit (slope {slope:.2f})")
    ax.errorbar(bctr, bmean, yerr=bstd, fmt="o", ms=9, color="k", mfc="#c0392b",
                mec="k", lw=1.4, capsize=3, zorder=6, label="This study, binned mean")
    ax.set(xlim=[5, 60], ylim=[5, 60], xlabel="Seismic Moho depth (km)",
           ylabel="Model Moho depth (km)", title="Model vs seismic Moho (N = 105)")
    ax.legend(frameon=False, loc="upper left", fontsize=9); ax.set_aspect("equal")
    fig.tight_layout(); fig.savefig(C.FIGURES / "scatter_vs_seismic.png", dpi=170)

    # ---- Fig: validation points + difference-from-CRUST1.0 + difference-from-GEMMA ----
    region = [94, 141, -11, 6.5]
    br = (region[3] - region[2]) / (region[1] - region[0])
    fine_lon = d.longitude.values; fine_lat = d.latitude.values
    LON, LAT = np.meshgrid(fine_lon, fine_lat)
    cr_grid = crust_i(np.column_stack([LAT.ravel(), LON.ravel()])).reshape(d.shape)
    diffs = [("(b) This study − CRUST1.0", d.values - cr_grid)]
    if "GEMMA" in models:
        g_grid = gi(np.column_stack([LAT.ravel(), LON.ravel()])).reshape(d.shape)
        diffs.append(("(c) This study − GEMMA", d.values - g_grid))

    def slimbar(pcm, ax, label):
        cax = ax.inset_axes([1.025, 0.27, 0.014, 0.46])   # slim, half the map height
        cb = fig.colorbar(pcm, cax=cax)
        cb.set_label(label, fontsize=8.5); cb.ax.tick_params(labelsize=7.5, length=2)
        cb.outline.set_linewidth(0.3)

    n = 1 + len(diffs)
    fig = plt.figure(figsize=(6.9 * n, 4.6))
    gs = fig.add_gridspec(1, n, wspace=0.42)
    ax1 = fig.add_subplot(gs[0], projection=ccrs.PlateCarree())
    ax1.set_extent(region); ax1.set_aspect("auto"); ax1.set_box_aspect(br)
    try:
        ax1.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#f4f1ea")
        ax1.coastlines("50m", lw=0.4, color="0.4")
    except Exception:
        pass
    sc = ax1.scatter(slon, slat, c=sdep, cmap="viridis", s=30, edgecolor="k", lw=0.3,
                     transform=ccrs.PlateCarree())
    gl = ax1.gridlines(draw_labels=True, lw=0.2); gl.top_labels = gl.right_labels = False
    slimbar(sc, ax1, "seismic Moho (km)")
    ax1.set_title("(a) 105 receiver-function validation points")
    for k, (title, resid) in enumerate(diffs, start=1):
        axk = fig.add_subplot(gs[k], projection=ccrs.PlateCarree())
        axk.set_extent(region); axk.set_aspect("auto"); axk.set_box_aspect(br)
        pcm = axk.pcolormesh(fine_lon, fine_lat, resid, cmap="RdBu_r", vmin=-15, vmax=15,
                             shading="auto", transform=ccrs.PlateCarree())
        try:
            axk.coastlines("50m", lw=0.4, color="0.25")
        except Exception:
            pass
        gl = axk.gridlines(draw_labels=True, lw=0.2); gl.top_labels = gl.right_labels = False
        slimbar(pcm, axk, "difference (km)")
        axk.set_title(title)
    fig.savefig(C.FIGURES / "compare_global_models.png", dpi=170, bbox_inches="tight")
    print("Wrote scatter_vs_seismic.png, compare_global_models.png, compare_global_models.txt")


if __name__ == "__main__":
    main()
