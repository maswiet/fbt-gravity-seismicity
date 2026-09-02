"""
20 — Acquire satellite gravity + bathymetry/topography for Teluk Tomini.

Sources (public, no login for the default path):
  gravity  : GMT `earth_faa` 1-arc-min free-air anomaly (Sandwell & Smith
             altimetry, served through GMT/GSHHG) — offshore backbone.
  topo     : GMT `earth_relief` 15-arc-sec bathymetry/topography.

Alternatives (set C.GRAVITY_SOURCE):
  "sandwell": place a cropped Sandwell grid (grav_*.nc) in C.GRAVITY_RAW; this
              script will read + resample it.
  "ggm"     : synthesise the XGM2019e gravity disturbance with pyshtools
              (reuses ../moho_indonesia/ggm_gravity.py).

Everything is resampled onto the padded model grid and saved as NetCDF.

Run (in the fbt env):  python basin_tomini/20_fetch_gravity_topo.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, bu


def _model_grid():
    lon, lat = bu.make_grid_coordinates(C.REGION_PADDED, C.SPACING)
    return lon, lat


def fetch_topography(lon, lat):
    import pygmt
    import xarray as xr
    grid = pygmt.datasets.load_earth_relief(
        resolution="15s", region=list(C.REGION_PADDED))
    da = grid.interp(lon=lon[0, :], lat=lat[:, 0], method="linear")
    filled = bu.fill_nan_nearest(da.values)   # close padded-edge gaps
    da = xr.DataArray(filled, coords={"latitude": lat[:, 0],
                      "longitude": lon[0, :]}, dims=("latitude", "longitude"),
                      name="topography", attrs={"units": "m", "datum": "sea level, +up"})
    da.to_netcdf(C.GRID_TOPO)
    print("Wrote", C.GRID_TOPO, "| range (m):",
          float(np.nanmin(da)), "..", float(np.nanmax(da)))
    return da


def fetch_gravity_gmt(lon, lat):
    """GMT earth_faa (Sandwell altimetry) free-air anomaly, resampled."""
    import pygmt
    grid = pygmt.datasets.load_earth_free_air_anomaly(
        resolution="01m", region=list(C.REGION_PADDED))
    da = grid.interp(lon=lon[0, :], lat=lat[:, 0], method="linear")
    return bu.save_grid(bu.fill_nan_nearest(da.values), lon, lat, C.GRID_FAA,
                        "free_air_anomaly",
                        attrs={"units": "mGal", "source": "GMT earth_faa 01m"})


def fetch_gravity_sandwell(lon, lat):
    """Read a manually-downloaded Sandwell grid from C.GRAVITY_RAW and resample."""
    import xarray as xr
    cands = sorted(C.GRAVITY_RAW.glob("grav_*.nc")) + sorted(C.GRAVITY_RAW.glob("*sandwell*.nc"))
    if not cands:
        raise FileNotFoundError(
            f"No Sandwell grid in {C.GRAVITY_RAW}. Download grav_32.1.nc from "
            "https://topex.ucsd.edu/pub/global_grav_1min/ and crop to the region.")
    ds = xr.open_dataset(cands[0])
    var = list(ds.data_vars)[0]
    da = ds[var]
    rename = {c: n for c, n in (("x", "longitude"), ("lon", "longitude"),
              ("y", "latitude"), ("lat", "latitude")) if c in da.coords}
    da = da.rename(rename).sortby("latitude")
    da = da.interp(longitude=lon[0, :], latitude=lat[:, 0], method="linear")
    return bu.save_grid(bu.fill_nan_nearest(da.values), lon, lat, C.GRID_FAA,
                        "free_air_anomaly",
                        attrs={"units": "mGal", "source": cands[0].name})


def fetch_gravity_ggm(lon, lat):
    """XGM2019e gravity disturbance via pyshtools (reused from moho_indonesia)."""
    import ggm_gravity  # on sys.path via _bootstrap (moho_indonesia)
    dist = ggm_gravity.fetch_ggm_disturbance(
        lon, lat, lmax=C.GGM_MAX_DEGREE, height_m=C.COMPUTATION_HEIGHT,
        model=C.GGM_NAME)
    return bu.save_grid(bu.fill_nan_nearest(dist), lon, lat, C.GRID_FAA, "free_air_anomaly",
                        attrs={"units": "mGal",
                               "source": f"{C.GGM_NAME} disturbance d/o {C.GGM_MAX_DEGREE}"})


def main() -> None:
    C.ensure_dirs()
    lon, lat = _model_grid()
    print(f"Model grid: {lon.shape} @ {C.SPACING} deg over {C.REGION_PADDED}")
    fetch_topography(lon, lat)
    src = C.GRAVITY_SOURCE
    if src == "gmt":
        g = fetch_gravity_gmt(lon, lat)
    elif src == "sandwell":
        g = fetch_gravity_sandwell(lon, lat)
    elif src == "ggm":
        g = fetch_gravity_ggm(lon, lat)
    else:
        raise ValueError(f"unknown GRAVITY_SOURCE: {src}")
    print("Wrote", C.GRID_FAA, "| range (mGal):",
          float(np.nanmin(g)), "..", float(np.nanmax(g)))


if __name__ == "__main__":
    main()
