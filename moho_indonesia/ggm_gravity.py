"""
GGM gravity disturbance from a satellite spherical-harmonic model (pyshtools).

This is the "exact paper" gravity source: the gravity disturbance synthesised
from a satellite Global Gravity Model (GOCO06S — the successor of the paper's
GOCO5S), rather than the altimetry free-air anomaly proxy.

Key detail: the disturbance must be evaluated ON the reference ellipsoid (WGS84)
with Earth rotation (omega) set, so the normal gravity cancels correctly. We
evaluate on a surface raised by `height_m` so it is consistent with the constant
computation height used by the tesseroid corrections/inversion.
"""
from __future__ import annotations

import numpy as np


def fetch_ggm_disturbance(lon2d, lat2d, lmax=300, height_m=4000.0, model="GOCO06S"):
    """Return the GGM gravity disturbance (mGal) on the model grid.

    Parameters
    ----------
    lon2d, lat2d : 2D model-grid coordinate arrays (degrees).
    lmax : maximum spherical-harmonic degree (satellite models ~ 200-300).
    height_m : constant height above the ellipsoid (must match the tesseroid
        computation height used elsewhere in the pipeline).
    model : a name in pyshtools.datasets.Earth (e.g. GOCO06S, XGM2019E, EGM2008).
    """
    import pyshtools as pysh
    from scipy.interpolate import RegularGridInterpolator

    wgs = pysh.constants.Earth.wgs84
    clm = getattr(pysh.datasets.Earth, model)(lmax=lmax)
    clm.omega = wgs.omega.value                      # ensure centrifugal term
    grav = clm.expand(a=wgs.a.value + height_m, f=wgs.f.value,
                      lmax=lmax, normal_gravity=True)
    disturbance = grav.total.data * 1e5              # m/s^2 -> mGal
    lats = grav.total.lats()
    lons = grav.total.lons()                         # 0..360

    interp = RegularGridInterpolator((lats[::-1], lons), disturbance[::-1, :],
                                     bounds_error=False, fill_value=np.nan)
    lon1d = np.asarray(lon2d)[0, :] % 360.0
    lat1d = np.asarray(lat2d)[:, 0]
    LON, LAT = np.meshgrid(lon1d, lat1d)
    return interp(np.column_stack([LAT.ravel(), LON.ravel()])).reshape(lon2d.shape)
