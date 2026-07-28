"""
Shared helpers for the Indonesia Moho gravity-inversion pipeline.

Grid I/O, tesseroid-model construction, the smoothness (roughness) matrix, and
data loading. Kept dependency-light so every numbered script can import it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import verde as vd
import xarray as xr

try:                       # works both as a package and when run from this folder
    from . import config as C
except ImportError:
    import config as C


# --------------------------------------------------------------------------
# Grid helpers
# --------------------------------------------------------------------------
def make_grid_coordinates(region=C.REGION_PADDED, spacing=C.SPACING):
    """Return (longitude, latitude) 2D arrays for the model/data grid.

    Uses verde.grid_coordinates so the grid is regular, which the Bott/Gauss-
    Newton inversion (regular-mesh requirement) depends on.
    """
    longitude, latitude = vd.grid_coordinates(region=region, spacing=spacing)
    return longitude, latitude


def save_grid(data: np.ndarray, longitude: np.ndarray, latitude: np.ndarray,
              path: Path, name: str, attrs: dict | None = None) -> xr.DataArray:
    """Save a 2D field as a CF-style NetCDF DataArray and return it."""
    da = xr.DataArray(
        data,
        coords={"latitude": latitude[:, 0], "longitude": longitude[0, :]},
        dims=("latitude", "longitude"),
        name=name,
        attrs=attrs or {},
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    da.to_netcdf(path)
    return da


def load_grid(path: Path) -> xr.DataArray:
    """Load a NetCDF grid saved by save_grid()."""
    return xr.open_dataarray(path)


# --------------------------------------------------------------------------
# Validation Moho points
# --------------------------------------------------------------------------
def load_seismic_moho(path: Path = C.MOHO_SEISMIC) -> pd.DataFrame:
    """Load the seismic Moho compilation (STAT LON LAT DEPTH, tab-separated).

    Returns a DataFrame with columns: station, longitude, latitude, depth_km.
    DEPTH is Moho depth in km (positive down). TODO: confirm the depth datum
    (sea level vs ellipsoid) with the data provider before validation.
    """
    df = pd.read_csv(path, sep=r"\s+", comment="#",
                     names=["station", "longitude", "latitude", "depth_km"],
                     header=0)
    df = df.dropna().reset_index(drop=True)
    return df


# --------------------------------------------------------------------------
# Tesseroid model of the anomalous Moho
# --------------------------------------------------------------------------
def moho_to_tesseroids(moho_depth_km: np.ndarray,
                       longitude: np.ndarray,
                       latitude: np.ndarray,
                       z_ref_km: float,
                       drho: float):
    """Build a tesseroid model of the anomalous Moho relief.

    Each tesseroid spans one grid cell horizontally and, vertically, the gap
    between the reference Moho (z_ref) and the actual Moho depth. Where the Moho
    is deeper than z_ref the density contrast is +drho; where shallower it is
    -drho (see paper Fig. 1f).

    Returns a structure suitable for harmonica.tesseroid_gravity.
    TODO: implement using boule.WGS84 mean radius and harmonica tesseroid
    boundaries (w, e, s, n, bottom, top) with a per-tesseroid density array.
    """
    raise NotImplementedError("Build tesseroid boundaries + density array here.")


def bouguer_plate_jacobian(drho: float) -> float:
    """Diagonal Bott/Gauss-Newton Jacobian value A = 2*pi*G*drho (eq. 15).

    G in SI; result in mGal per metre of relief when relief is in metres.
    """
    G = 6.67430e-11           # m^3 kg^-1 s^-2
    mgal = 1e5                # 1 m/s^2 = 1e5 mGal
    return 2.0 * np.pi * G * drho * mgal


# --------------------------------------------------------------------------
# First-order smoothness (roughness) matrix R  (Tikhonov, eq. 9)
# --------------------------------------------------------------------------
def finite_difference_matrix(n_lat: int, n_lon: int):
    """Sparse first-order finite-difference matrix over a regular n_lat x n_lon grid.

    Rows encode differences between horizontally- and vertically-adjacent
    parameters, so that R^T R penalises roughness of the Moho relief.
    Returns a scipy.sparse matrix of shape (n_edges, n_lat*n_lon).
    TODO: assemble the edge list for both grid directions.
    """
    raise NotImplementedError("Assemble the sparse first-difference matrix.")
