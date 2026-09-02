"""
Tahap 4-5 — RF-constrained satellite-gravity sediment-thickness model.

Idea (the "bridge" from seismology to basin exploration):
  * Satellite gravity (GGM+WGM Bouguer) gives dense, continuous spatial coverage
    but is non-unique (needs a density/depth calibration).
  * MERAMEX receiver functions give ABSOLUTE, physically-anchored sediment
    thickness at ~100 points, but only at stations.
  Combine them: calibrate the residual Bouguer against the RF sediment thickness,
  map thickness everywhere from gravity, then TIE the map back to the RF points
  (collocation) so the final model honours the seismology and fills the gaps.

Inputs : data/processed/rf_java/bouguer_cjava.nc, sediment_rf.csv
Outputs: data/processed/rf_java/sediment_thickness_grav.nc
         figures/rf_java/{bouguer,residual,rf_vs_gravity,sediment_constrained}.png
Run:  python rf_gravity_java/rf_gravity_join.py
"""
from __future__ import annotations

import sys
import pathlib

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C

REGIONAL_SIGMA_KM = 40.0     # Gaussian regional wavelength for residual separation
TIE_CORR_KM = 25.0           # correlation length for the RF collocation tie


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd
    import xarray as xr
    from scipy.ndimage import gaussian_filter
    from scipy.interpolate import RBFInterpolator

    C.ensure_dirs()
    g = xr.open_dataarray(C.DATA_PROCESSED / "bouguer_cjava.nc")
    if "x" in g.dims:
        g = g.rename({"x": "lon", "y": "lat"})
    elif "longitude" in g.dims:
        g = g.rename({"longitude": "lon", "latitude": "lat"})
    lon = g["lon"].values; lat = g["lat"].values
    boug = g.values.astype(float)
    dlat_km = 111.0 * (lat[1] - lat[0])
    sig_pix = REGIONAL_SIGMA_KM / abs(dlat_km)
    regional = gaussian_filter(boug, sigma=sig_pix, mode="nearest")
    residual = boug - regional

    sed = pd.read_csv(C.SEDIMENT_CSV)
    sed = sed[(sed.kind.isin(["EDL", "SAM"])) & (sed.h_sed_km > 0)].copy()
    # Sample residual Bouguer at station locations.
    def samp(field, lo, la):
        i = np.clip(np.searchsorted(lat, la), 0, len(lat)-1)
        j = np.clip(np.searchsorted(lon, lo), 0, len(lon)-1)
        return field[i, j]
    sed["res"] = [samp(residual, r.lon, r.lat) for _, r in sed.iterrows()]

    # Robust linear calibration H_RF = a*res + b (expect a<0).
    a, b = np.polyfit(sed["res"], sed["h_sed_km"], 1)
    corr = np.corrcoef(sed["res"], sed["h_sed_km"])[0, 1]
    print(f"Calibration H = {a:.4f}*resBouguer + {b:.3f}  (r = {corr:.2f}, "
          f"n={len(sed)})")

    LON, LAT = np.meshgrid(lon, lat)
    h_grav = a * residual + b                      # gravity-predicted thickness

    # RF tie (collocation): interpolate station residuals (H_RF - H_grav_pred)
    # with a Gaussian RBF, add back so the model honours the RF points.
    dres = sed["h_sed_km"].values - (a * sed["res"].values + b)
    pts = np.column_stack([sed.lon.values, sed.lat.values])
    eps = TIE_CORR_KM / 111.0
    rbf = RBFInterpolator(pts, dres, kernel="gaussian", epsilon=1.0/eps,
                          smoothing=0.5)
    tie = rbf(np.column_stack([LON.ravel(), LAT.ravel()])).reshape(LON.shape)
    h_final = np.clip(h_grav + tie, 0, None)

    da = xr.DataArray(h_final, coords={"lat": lat, "lon": lon},
                      dims=("lat", "lon"), name="sediment_thickness_km",
                      attrs={"units": "km", "method": "RF-calibrated GGM+WGM "
                             "Bouguer residual, tied to RF stations",
                             "calib_a": a, "calib_b": b, "calib_r": corr})
    da.to_netcdf(C.GRID_SED_GRAV)

    # ---- Figures ----------------------------------------------------------
    ext = [lon.min(), lon.max(), lat.min(), lat.max()]
    def _map(field, title, cbar, cmap, fname, pts_c=None, vlim=None):
        fig, ax = plt.subplots(figsize=(8, 6.5))
        kw = dict(extent=ext, origin="lower", cmap=cmap, aspect=1.0)
        if vlim: kw.update(vmin=vlim[0], vmax=vlim[1])
        im = ax.imshow(field, **kw)
        if pts_c is not None:
            ax.scatter(sed.lon, sed.lat, c=pts_c, cmap=cmap, s=28,
                       edgecolor="k", lw=.4, vmin=kw.get("vmin"), vmax=kw.get("vmax"))
        plt.colorbar(im, label=cbar)
        ax.set_title(title); ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        fig.tight_layout(); fig.savefig(C.FIGURES / fname, dpi=200); plt.close(fig)
        print("Wrote", C.FIGURES / fname)

    _map(boug, "GGM+WGM complete Bouguer anomaly — Central Java", "mGal",
         "turbo", "bouguer.png")
    _map(residual, f"Residual Bouguer ({REGIONAL_SIGMA_KM:.0f} km high-pass)",
         "mGal", "RdBu_r", "residual.png", vlim=(-40, 40))
    vmax = float(np.nanpercentile(h_final, 97))
    _map(h_final, "RF-constrained sediment thickness (gravity + receiver functions)",
         "Sediment thickness (km)", "turbo", "sediment_constrained.png",
         pts_c=sed.h_sed_km.values, vlim=(0, vmax))

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(sed["res"], sed["h_sed_km"], s=30, edgecolor="k")
    xs = np.linspace(sed["res"].min(), sed["res"].max(), 50)
    ax.plot(xs, a*xs + b, "r", label=f"H = {a:.3f}·res + {b:.2f}\n r = {corr:.2f}")
    ax.set_xlabel("Residual Bouguer (mGal)"); ax.set_ylabel("RF sediment thickness (km)")
    ax.set_title("Calibration: RF sediment vs satellite gravity"); ax.legend()
    ax.grid(alpha=.3); fig.tight_layout()
    fig.savefig(C.FIGURES / "rf_vs_gravity.png", dpi=200); plt.close(fig)
    print("Wrote", C.FIGURES / "rf_vs_gravity.png")
    print(f"Final sediment model: {float(np.nanmin(h_final)):.1f}–"
          f"{float(np.nanmax(h_final)):.1f} km; wrote {C.GRID_SED_GRAV}")


if __name__ == "__main__":
    main()
