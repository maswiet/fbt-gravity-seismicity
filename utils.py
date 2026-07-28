"""
utils.py — Helper functions untuk workflow FBT
"""
import numpy as np
import xarray as xr
import pandas as pd
from pathlib import Path

# Konstanta fisis
G = 6.6743e-11           # Konstanta gravitasi universal (m^3 kg^-1 s^-2)
RHO_CRUST = 2670.0       # Densitas kerak rata-rata (kg/m^3) — Bouguer reduction standar
RHO_WATER = 1030.0       # Densitas air laut (kg/m^3)
RHO_INFILL_MARINE = RHO_CRUST - RHO_WATER  # 1640 kg/m^3 — kontras Bouguer laut

# Bounding box default
BBOX_FBT = dict(west=114, east=124, south=-11, north=-7)


def crop_grid(da: xr.DataArray, bbox: dict = BBOX_FBT,
              lon_name: str = "lon", lat_name: str = "lat") -> xr.DataArray:
    """Crop xarray DataArray ke bounding box. Auto-handles ascending/descending lat."""
    lon_slice = slice(bbox["west"], bbox["east"])
    # Cek orientasi lat
    lat_vals = da[lat_name].values
    if lat_vals[0] > lat_vals[-1]:  # descending
        lat_slice = slice(bbox["north"], bbox["south"])
    else:
        lat_slice = slice(bbox["south"], bbox["north"])
    return da.sel({lon_name: lon_slice, lat_name: lat_slice})


def regrid_to_target(da: xr.DataArray, target_lon: np.ndarray,
                     target_lat: np.ndarray, method: str = "linear") -> xr.DataArray:
    """Regrid DataArray ke common grid. Method: 'linear' (smooth) atau 'nearest'."""
    return da.interp(lon=target_lon, lat=target_lat, method=method)


def make_target_grid(bbox: dict = BBOX_FBT, spacing: float = 0.02):
    """Generate target grid coordinates."""
    lon = np.arange(bbox["west"], bbox["east"] + spacing/2, spacing)
    lat = np.arange(bbox["south"], bbox["north"] + spacing/2, spacing)
    return lon, lat


def bouguer_slab_correction(topography_m: np.ndarray,
                             rho: float = RHO_CRUST,
                             rho_water: float = RHO_WATER) -> np.ndarray:
    """
    Hitung Bouguer slab correction (mGal).

    Untuk darat (topo > 0): -2πGρh (perlu dikurangkan dari free-air)
    Untuk laut (topo < 0):  +2πG(ρ-ρ_w)|h|  (perlu ditambahkan untuk
                            mengisi kolom air dengan kerak)

    Parameter
    ---------
    topography_m : array (m, positif darat, negatif laut)
    rho : densitas kerak (kg/m^3)
    rho_water : densitas air (kg/m^3)

    Return
    ------
    bc : Bouguer correction dalam mGal (sudah dengan tanda yang benar
         untuk dijumlahkan ke free-air anomaly)
    """
    # Faktor 2πG dalam unit mGal/(kg/m^3 · m) = 4.1919e-5 m^3/(kg s^2) -> mGal
    twopiG = 2 * np.pi * G * 1e5  # konversi ke mGal
    bc = np.where(
        topography_m >= 0,
        -twopiG * rho * topography_m,                        # darat
        +twopiG * (rho - rho_water) * np.abs(topography_m)   # laut (replace water with rock)
    )
    return bc


def normal_gravity_wgs84(latitude_deg: np.ndarray) -> np.ndarray:
    """
    Normal gravity di permukaan WGS84 ellipsoid (mGal) — Somigliana formula.
    Untuk konversi gravitasi observasi ke gravity disturbance.
    """
    lat_rad = np.deg2rad(latitude_deg)
    sin2 = np.sin(lat_rad)**2
    # Konstanta WGS84
    ge = 978032.53359   # mGal di equator
    k = 0.00193185265241
    e2 = 0.00669437999014
    g = ge * (1 + k * sin2) / np.sqrt(1 - e2 * sin2)
    return g


def radial_power_spectrum(grid: xr.DataArray, dx_km: float):
    """
    Radial average power spectrum (Spector & Grant) untuk estimasi
    depth ke top of source dan separasi regional/residual.

    Return
    ------
    k : wavenumber (rad/km)
    P : power
    """
    z = grid.values - np.nanmean(grid.values)
    z = np.nan_to_num(z, nan=0.0)
    ny, nx = z.shape

    # 2D FFT
    F = np.fft.fft2(z)
    P2 = np.abs(F)**2 / (nx * ny)

    # Wavenumber grids
    kx = 2 * np.pi * np.fft.fftfreq(nx, d=dx_km)
    ky = 2 * np.pi * np.fft.fftfreq(ny, d=dx_km)
    KX, KY = np.meshgrid(kx, ky)
    K = np.sqrt(KX**2 + KY**2)

    # Radial bins
    k_max = K.max() / 2
    bins = np.linspace(0, k_max, 50)
    centers = 0.5 * (bins[:-1] + bins[1:])

    P_radial = np.zeros_like(centers)
    for i in range(len(centers)):
        mask = (K >= bins[i]) & (K < bins[i+1])
        if mask.any():
            P_radial[i] = P2[mask].mean()

    return centers, P_radial


def utm_zone_from_lon(lon: float) -> int:
    """Return UTM zone number untuk longitude tertentu."""
    return int((lon + 180) / 6) + 1


def haversine_km(lon1, lat1, lon2, lat2):
    """Jarak haversine dalam km."""
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlam = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))


def ensure_dir(path):
    """Pastikan direktori ada."""
    Path(path).mkdir(parents=True, exist_ok=True)
