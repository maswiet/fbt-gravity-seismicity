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

    g = -2*pi*G*drho * (moho_depth - z_ref). The minus sign matches the physical
    convention (deeper Moho -> mass deficit -> negative anomaly) and the tesseroid
    sign convention in `moho_to_tesseroids`. Used to (a) unit-test the inversion
    machinery without harmonica, and (b) provide a fast first-pass forward.
    `moho_depth_m` may be any shape; returns the same shape in mGal.
    """
    a = -bouguer_plate_jacobian(drho)
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
    # Paper Fig. 1f: Moho BELOW z_ref (deeper) -> the zone is crust where the
    # reference has mantle -> NEGATIVE density contrast; shallower -> positive.
    density = np.where(depth_m > z_ref_m, -drho, drho).astype(float)

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


def _cell_half_spacing(lon, lat):
    """Return (half-dlon, half-dlat) for a regular grid."""
    dlon = abs(lon[0, 1] - lon[0, 0]) / 2.0
    dlat = abs(lat[1, 0] - lat[0, 0]) / 2.0
    return dlon, dlat


def topography_to_tesseroids(topo_m, longitude, latitude,
                             density_land: float = C.RHO_CRUST,
                             density_water_contrast: float = C.RHO_OCEAN_CONTRAST):
    """Tesseroid model of topography + oceans for the Bouguer correction.

    Land cells (h>=0): tesseroid from the reference sphere R up to R+h, density
    `density_land` (2670). Ocean cells (h<0): tesseroid from the seafloor R+h up
    to R, density `density_water_contrast` (~ -1640 = rho_water - rho_crust).

    Returns (tesseroids[w,e,s,n,bottom,top], density) for harmonica.
    """
    lon = np.asarray(longitude, float)
    lat = np.asarray(latitude, float)
    h = np.asarray(topo_m, float).ravel()
    R = _mean_earth_radius()
    dlon, dlat = _cell_half_spacing(lon, lat)

    land = h >= 0
    bottom = np.where(land, R, R + h)
    top = np.where(land, R + h, R)
    density = np.where(land, density_land, density_water_contrast).astype(float)
    tesseroids = np.column_stack([lon.ravel() - dlon, lon.ravel() + dlon,
                                  lat.ravel() - dlat, lat.ravel() + dlat,
                                  bottom, top])
    return tesseroids, density


def layer_to_tesseroids(top_depth_m, bottom_depth_m, longitude, latitude,
                        density_contrast):
    """Tesseroid model of a subsurface layer (e.g. a sediment layer).

    Depths are positive-down from sea level; `top_depth < bottom_depth`.
    `density_contrast` may be a scalar or a per-cell array (kg/m^3), typically
    (rho_layer - rho_crust) so its effect can be *removed* from the Bouguer field.

    Returns (tesseroids[w,e,s,n,bottom,top], density) for harmonica.
    """
    lon = np.asarray(longitude, float)
    lat = np.asarray(latitude, float)
    td = np.asarray(top_depth_m, float).ravel()
    bd = np.asarray(bottom_depth_m, float).ravel()
    R = _mean_earth_radius()
    dlon, dlat = _cell_half_spacing(lon, lat)

    top_radius = R - td            # shallower depth -> larger radius
    bottom_radius = R - bd
    bottom = np.minimum(bottom_radius, top_radius)
    top = np.maximum(bottom_radius, top_radius)
    density = np.broadcast_to(np.ravel(np.asarray(density_contrast, float)),
                              td.shape).astype(float)
    tesseroids = np.column_stack([lon.ravel() - dlon, lon.ravel() + dlon,
                                  lat.ravel() - dlat, lat.ravel() + dlat,
                                  bottom, top])
    return tesseroids, density


def tesseroid_gravity_grid(tesseroids, density, longitude, latitude,
                           height_m: float = C.COMPUTATION_HEIGHT):
    """Forward model g_z (mGal) of a tesseroid model onto the 2D grid.

    Requires harmonica + boule (the `fbt` environment).
    """
    import harmonica as hm
    lon = np.asarray(longitude, float)
    lat = np.asarray(latitude, float)
    R = _mean_earth_radius()
    coordinates = (lon.ravel(), lat.ravel(), np.full(lon.size, R + height_m))
    g = hm.tesseroid_gravity(coordinates, tesseroids, density, field="g_z")
    return np.asarray(g).reshape(lon.shape)


def load_crust1_sediments(model_longitude, model_latitude, crust1_dir=C.CRUST1_DIR):
    """Read CRUST1.0 sediment layers and resample onto the model grid.

    CRUST1.0 (Laske et al. 2013) is a 1x1 degree, 8-layer global model. Files:
      crust1.bnds — 9 boundary depths (km, +up) per cell, ordered N->S, W->E,
                    from 89.5N/-179.5E; layers: water, ice, upper/middle/lower
                    sediments, upper/middle/lower crust (+ top of mantle = Moho).
      crust1.rho  — 8 layer densities (g/cm^3) per cell, same ordering.

    Returns a list of three dicts (upper/middle/lower sediments), each with
    `top_depth_m`, `bottom_depth_m` (positive down, on the model grid) and
    `density_contrast` (rho_layer - RHO_CRUST, kg/m^3, on the model grid).

    TODO(verify): confirm the exact column order and sign convention against the
    downloaded CRUST1.0 files before trusting the sediment correction.
    """
    import pathlib
    from scipy.interpolate import RegularGridInterpolator

    bnds = np.loadtxt(pathlib.Path(crust1_dir) / "crust1.bnds")
    rho = np.loadtxt(pathlib.Path(crust1_dir) / "crust1.rho")
    n_lat_c, n_lon_c = 180, 360
    # CRUST1.0 native grid centres.
    clat = np.arange(89.5, -90.0, -1.0)      # 89.5 -> -89.5
    clon = np.arange(-179.5, 180.0, 1.0)     # -179.5 -> 179.5
    bnds = bnds.reshape(n_lat_c, n_lon_c, -1)
    rho = rho.reshape(n_lat_c, n_lon_c, -1)

    # Sediment layers occupy boundary/rho indices 2,3,4 (0-based): upper/middle/lower.
    sed_idx = [2, 3, 4]
    mlon = np.asarray(model_longitude, float)
    mlat = np.asarray(model_latitude, float)
    pts = np.column_stack([mlat.ravel(), mlon.ravel()])

    def sample(field2d):
        interp = RegularGridInterpolator(
            (clat[::-1], clon), field2d[::-1, :],
            bounds_error=False, fill_value=None)
        return interp(pts).reshape(mlon.shape)

    layers = []
    for k in sed_idx:
        top_km = sample(bnds[:, :, k])        # boundary depth (km, +up)
        bot_km = sample(bnds[:, :, k + 1])
        dens = sample(rho[:, :, k]) * 1000.0  # g/cm^3 -> kg/m^3
        # Absent layers have rho==0 in CRUST1.0; give them zero contrast so they
        # never contribute (their thickness is ~0 anyway).
        contrast = np.where(dens > 0, dens - C.RHO_CRUST, 0.0)
        layers.append({
            "top_depth_m": -top_km * 1000.0,          # +up -> +down
            "bottom_depth_m": -bot_km * 1000.0,
            "density_contrast": contrast,
        })
    return layers


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
