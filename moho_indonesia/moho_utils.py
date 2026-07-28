"""
Shared helpers for the Indonesia Moho gravity-inversion pipeline.

Grid I/O, tesseroid-model construction, the smoothness (roughness) matrix, and
data loading. Heavy geophysics deps (verde/xarray/harmonica/boule) are imported
lazily inside the functions that need them, so the pure-algorithm core (numpy +
scipy) can be imported and unit-tested without the full `fbt` environment.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.sparse as sp

try:                       # works both as a package and when run from this folder
    from . import config as C
except ImportError:
    import config as C


# --------------------------------------------------------------------------
# Grid helpers
# --------------------------------------------------------------------------
def make_grid_coordinates(region=C.REGION_PADDED, spacing=C.SPACING):
    """Return (longitude, latitude) 2D arrays for the regular model/data grid."""
    import verde as vd
    return vd.grid_coordinates(region=region, spacing=spacing)


def save_grid(data, longitude, latitude, path: Path, name: str, attrs=None):
    """Save a 2D field as a CF-style NetCDF DataArray and return it."""
    import xarray as xr
    data = np.asarray(data)
    da = xr.DataArray(
        data,
        coords={"latitude": np.asarray(latitude)[:, 0],
                "longitude": np.asarray(longitude)[0, :]},
        dims=("latitude", "longitude"),
        name=name,
        attrs=attrs or {},
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    da.to_netcdf(path)
    return da


def load_grid(path: Path):
    """Load a NetCDF grid saved by save_grid()."""
    import xarray as xr
    return xr.open_dataarray(path)


# --------------------------------------------------------------------------
# Validation Moho points
# --------------------------------------------------------------------------
def load_seismic_moho(path: Path = C.MOHO_SEISMIC) -> pd.DataFrame:
    """Load the seismic Moho compilation (STAT LON LAT DEPTH, whitespace-sep).

    Returns columns: station, longitude, latitude, depth_km (positive down).
    TODO: confirm the depth datum (sea level vs ellipsoid) with the provider.
    """
    df = pd.read_csv(path, sep=r"\s+", comment="#",
                     names=["station", "longitude", "latitude", "depth_km"],
                     header=0)
    return df.dropna().reset_index(drop=True)


# --------------------------------------------------------------------------
# Bott / Gauss-Newton Jacobian (eq. 15)
# --------------------------------------------------------------------------
def bouguer_plate_jacobian(drho: float) -> float:
    """Diagonal Jacobian value A = 2*pi*G*drho (eq. 15).

    Units: mGal per metre of relief (drho in kg/m^3).
    """
    G = 6.67430e-11           # m^3 kg^-1 s^-2
    mgal = 1e5                # 1 m/s^2 = 1e5 mGal
    return 2.0 * np.pi * G * drho * mgal


def forward_gravity_bouguer_plate(moho_depth_m, z_ref_m: float, drho: float):
    """Cheap linear forward model: the Bouguer-plate response of the relief.

    g = 2*pi*G*drho * (moho_depth - z_ref). This is the approximation Bott's
    method is built on; used to (a) unit-test the inversion machinery without
    harmonica, and (b) provide a fast first-pass forward. `moho_depth_m` may be
    any shape; returns the same shape in mGal.
    """
    a = bouguer_plate_jacobian(drho)
    return a * (np.asarray(moho_depth_m, dtype=float) - z_ref_m)


# --------------------------------------------------------------------------
# Tesseroid model of the anomalous Moho (real, spherical forward model)
# --------------------------------------------------------------------------
def _mean_earth_radius() -> float:
    try:
        import boule as bl
        return float(bl.WGS84.mean_radius)
    except Exception:
        return 6_371_000.0    # fallback spherical radius (m)


def moho_to_tesseroids(moho_depth_km, longitude, latitude,
                       z_ref_km: float, drho: float):
    """Build a tesseroid model of the anomalous Moho relief (paper Fig. 1f).

    Each grid cell becomes one tesseroid spanning the gap between the reference
    Moho (radius R - z_ref) and the actual Moho (radius R - moho_depth). Cells
    where the Moho is deeper than z_ref get density +drho; shallower get -drho.

    Returns (tesseroids, density) ready for harmonica.tesseroid_gravity, where
    tesseroids has columns [w, e, s, n, bottom, top] (lon/lat degrees; bottom/top
    radii in metres from the geocentre).
    """
    lon = np.asarray(longitude, dtype=float)
    lat = np.asarray(latitude, dtype=float)
    depth_m = np.asarray(moho_depth_km, dtype=float).ravel() * 1000.0
    z_ref_m = z_ref_km * 1000.0
    R = _mean_earth_radius()

    # Half cell size (assumes a regular grid).
    dlon = abs(lon[0, 1] - lon[0, 0]) / 2.0
    dlat = abs(lat[1, 0] - lat[0, 0]) / 2.0
    w = lon.ravel() - dlon
    e = lon.ravel() + dlon
    s = lat.ravel() - dlat
    n = lat.ravel() + dlat

    # Deeper Moho -> smaller radius. bottom < top.
    radius_moho = R - depth_m
    radius_ref = R - z_ref_m
    bottom = np.minimum(radius_moho, radius_ref)
    top = np.maximum(radius_moho, radius_ref)
    density = np.where(depth_m > z_ref_m, drho, -drho).astype(float)

    tesseroids = np.column_stack([w, e, s, n, bottom, top])
    return tesseroids, density


def make_tesseroid_forward(longitude, latitude, height_m=C.COMPUTATION_HEIGHT):
    """Return a callable p_1d(metres) -> predicted gravity (mGal, 1D) using tesseroids.

    Closes over the observation coordinates so the inversion can call it each
    iteration. Requires harmonica + boule (the `fbt` environment).
    """
    import harmonica as hm

    lon = np.asarray(longitude, dtype=float)
    lat = np.asarray(latitude, dtype=float)
    R = _mean_earth_radius()
    obs_radius = np.full(lon.size, R + height_m)
    coordinates = (lon.ravel(), lat.ravel(), obs_radius)
    shape = lon.shape

    def forward(p_metres, z_ref_km, drho):
        moho_km = np.asarray(p_metres, dtype=float).reshape(shape) / 1000.0
        tesseroids, density = moho_to_tesseroids(
            moho_km, lon, lat, z_ref_km=z_ref_km, drho=drho)
        g = hm.tesseroid_gravity(coordinates, tesseroids, density, field="g_z")
        return np.asarray(g)

    return forward


# --------------------------------------------------------------------------
# First-order smoothness (roughness) matrix R  (Tikhonov, eq. 9)
# --------------------------------------------------------------------------
def finite_difference_matrix(n_lat: int, n_lon: int) -> sp.csr_matrix:
    """Sparse first-order finite-difference matrix over a regular n_lat x n_lon grid.

    Each row encodes the difference between two adjacent parameters (horizontal
    and vertical neighbours), so R^T R penalises the roughness of the Moho relief.
    Returns a csr_matrix of shape (n_edges, n_lat*n_lon).
    """
    def idx(i, j):
        return i * n_lon + j

    rows, cols, vals = [], [], []
    r = 0
    # Horizontal neighbours (same row, adjacent columns).
    for i in range(n_lat):
        for j in range(n_lon - 1):
            rows += [r, r]; cols += [idx(i, j), idx(i, j + 1)]; vals += [1.0, -1.0]; r += 1
    # Vertical neighbours (adjacent rows, same column).
    for i in range(n_lat - 1):
        for j in range(n_lon):
            rows += [r, r]; cols += [idx(i, j), idx(i + 1, j)]; vals += [1.0, -1.0]; r += 1

    return sp.csr_matrix((vals, (rows, cols)), shape=(r, n_lat * n_lon))
