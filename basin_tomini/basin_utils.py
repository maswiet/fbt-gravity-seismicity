"""
Shared helpers for the Teluk Tomini / Gorontalo basin-delineation pipeline.

Two layers:

1. A pure-numpy potential-field core (FFT derivatives, edge detectors, upward
   continuation, polynomial trend). It needs only numpy/scipy so it can be
   imported and unit-tested WITHOUT the full `fbt` environment:

       python basin_tomini/basin_utils.py --selftest

2. Thin wrappers over the geospatial stack (xarray/verde/pyproj) for grid I/O
   and projecting a geographic grid to metres before the FFT transforms. These
   import their heavy deps lazily.

Convention: z is positive UP. For a potential field on a plane, the first
vertical derivative is |k|*F and upward continuation by h>0 is exp(-|k|h)*F in
the wavenumber domain (Blakely 1995).

References for the edge detectors
  THD  Total horizontal derivative        Cordell & Grauch (1985)
  TDR  Tilt derivative                     Miller & Singh (1994)
  ASA  Analytic signal / total gradient    Roest et al. (1992)
  THETA Theta map                          Wijns et al. (2005)
  tilt-depth depth-to-contact from TDR     Salem et al. (2007)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

try:                       # works as a package or when run from this folder
    from . import config as C
except ImportError:
    import config as C


# ==========================================================================
# Pure-numpy potential-field core (FFT-based)
# ==========================================================================
def _wavenumbers(shape, dx, dy):
    """Angular wavenumber grids (rad/m) for a regular ny x nx grid.

    Returns (kx, ky, k) where k = sqrt(kx^2 + ky^2). dx, dy are the grid
    spacings in metres along the x (easting) and y (northing) axes.
    """
    ny, nx = shape
    kx = 2.0 * np.pi * np.fft.fftfreq(nx, d=dx)
    ky = 2.0 * np.pi * np.fft.fftfreq(ny, d=dy)
    KX, KY = np.meshgrid(kx, ky)
    K = np.sqrt(KX**2 + KY**2)
    return KX, KY, K


def _mirror_pad(field, pad):
    """Reflect-pad to reduce FFT edge/wrap-around effects. Returns (padded, slc)."""
    if pad <= 0:
        return field, (slice(None), slice(None))
    padded = np.pad(field, pad, mode="reflect")
    slc = (slice(pad, pad + field.shape[0]), slice(pad, pad + field.shape[1]))
    return padded, slc


def derivative(field, dx, dy, direction, pad_frac=0.25):
    """First spatial derivative of a 2D field via FFT.

    direction: 'x' (easting), 'y' (northing) or 'z' (vertical, +up).
    dx, dy in metres. Returns an array with the same shape and units/m.
    """
    field = np.asarray(field, dtype=float)
    pad = int(pad_frac * max(field.shape))
    padded, slc = _mirror_pad(field, pad)
    KX, KY, K = _wavenumbers(padded.shape, dx, dy)
    F = np.fft.fft2(padded)
    if direction == "x":
        op = 1j * KX
    elif direction == "y":
        op = 1j * KY
    elif direction == "z":
        op = K                      # first vertical derivative (z positive up)
    else:
        raise ValueError("direction must be 'x', 'y' or 'z'")
    out = np.real(np.fft.ifft2(F * op))
    return out[slc]


def upward_continuation(field, dx, dy, height_m, pad_frac=0.5):
    """Upward-continue a field by height_m (>0) metres: multiply by exp(-|k|h)."""
    field = np.asarray(field, dtype=float)
    pad = int(pad_frac * max(field.shape))
    padded, slc = _mirror_pad(field, pad)
    _, _, K = _wavenumbers(padded.shape, dx, dy)
    F = np.fft.fft2(padded)
    out = np.real(np.fft.ifft2(F * np.exp(-K * float(height_m))))
    return out[slc]


def total_horizontal_derivative(field, dx, dy):
    """THD = sqrt(fx^2 + fy^2). Maxima trace edges/contacts (faults, basin flanks)."""
    fx = derivative(field, dx, dy, "x")
    fy = derivative(field, dx, dy, "y")
    return np.sqrt(fx**2 + fy**2)


def analytic_signal_amplitude(field, dx, dy):
    """ASA / total-gradient amplitude = sqrt(fx^2 + fy^2 + fz^2)."""
    fx = derivative(field, dx, dy, "x")
    fy = derivative(field, dx, dy, "y")
    fz = derivative(field, dx, dy, "z")
    return np.sqrt(fx**2 + fy**2 + fz**2)


def tilt_derivative(field, dx, dy):
    """TDR = atan2(fz, THD), in DEGREES.

    ~0 over an edge, positive over the source, negative off the source. Its zero
    contour maps edges independent of anomaly amplitude (Miller & Singh 1994).
    """
    fx = derivative(field, dx, dy, "x")
    fy = derivative(field, dx, dy, "y")
    fz = derivative(field, dx, dy, "z")
    thd = np.sqrt(fx**2 + fy**2)
    return np.degrees(np.arctan2(fz, thd))


def theta_map(field, dx, dy):
    """Theta map = THD / ASA (i.e. cos(theta)), in [0, 1].

    Minima (troughs) trace edges; used like THD but normalised, so weak and
    strong anomalies show comparably (Wijns et al. 2005).
    """
    fx = derivative(field, dx, dy, "x")
    fy = derivative(field, dx, dy, "y")
    fz = derivative(field, dx, dy, "z")
    thd = np.sqrt(fx**2 + fy**2)
    asa = np.sqrt(fx**2 + fy**2 + fz**2)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(asa > 0, thd / asa, np.nan)


def polynomial_trend(field, dx, dy, degree=3):
    """Least-squares 2D polynomial trend surface (a common 'regional' estimate)."""
    field = np.asarray(field, dtype=float)
    ny, nx = field.shape
    xs = (np.arange(nx) - nx / 2.0) * dx
    ys = (np.arange(ny) - ny / 2.0) * dy
    X, Y = np.meshgrid(xs, ys)
    # Normalise to keep the design matrix well-conditioned.
    xn = X / (np.abs(X).max() or 1.0)
    yn = Y / (np.abs(Y).max() or 1.0)
    cols = [(xn**i) * (yn**j)
            for d in range(degree + 1) for i in range(d + 1) for j in [d - i]]
    A = np.column_stack([c.ravel() for c in cols])
    mask = np.isfinite(field.ravel())
    coef, *_ = np.linalg.lstsq(A[mask], field.ravel()[mask], rcond=None)
    return (A @ coef).reshape(field.shape)


def separate_regional_residual(field, dx, dy, method=None,
                               upward_height_m=None, poly_degree=None,
                               gaussian_cut_m=None):
    """Split a field into (regional, residual). residual = field - regional."""
    method = method or C.SEPARATION_METHOD
    if method == "upward":
        h = C.UPWARD_HEIGHT_M if upward_height_m is None else upward_height_m
        regional = upward_continuation(field, dx, dy, h)
    elif method == "polynomial":
        d = C.POLY_DEGREE if poly_degree is None else poly_degree
        regional = polynomial_trend(field, dx, dy, degree=d)
    elif method == "gaussian":
        cut = C.GAUSSIAN_CUT_M if gaussian_cut_m is None else gaussian_cut_m
        regional = _gaussian_lowpass(field, dx, dy, cut)
    else:
        raise ValueError(f"unknown separation method: {method}")
    return regional, field - regional


def _gaussian_lowpass(field, dx, dy, cut_wavelength_m, pad_frac=0.5):
    """Gaussian low-pass: keep wavelengths longer than cut_wavelength_m."""
    field = np.asarray(field, dtype=float)
    pad = int(pad_frac * max(field.shape))
    padded, slc = _mirror_pad(field, pad)
    _, _, K = _wavenumbers(padded.shape, dx, dy)
    kc = 2.0 * np.pi / float(cut_wavelength_m)
    F = np.fft.fft2(padded)
    out = np.real(np.fft.ifft2(F * np.exp(-(K**2) / (2.0 * kc**2))))
    return out[slc]


# ==========================================================================
# Geospatial wrappers (lazy heavy deps): grid I/O + projection to metres
# ==========================================================================
def fill_nan_nearest(a):
    """Fill NaNs by nearest-neighbour (for padded-edge gaps after interpolation).

    A single NaN cell in a tesseroid model poisons the whole forward sum, and
    NaNs break the FFT transforms — so grids must be gap-free before use.
    """
    from scipy import ndimage
    a = np.asarray(a, dtype=float)
    mask = np.isnan(a)
    if not mask.any():
        return a
    idx = ndimage.distance_transform_edt(
        mask, return_distances=False, return_indices=True)
    return a[tuple(idx)]


def make_grid_coordinates(region=C.REGION_PADDED, spacing=C.SPACING):
    """(longitude, latitude) 2D arrays for the regular geographic model grid."""
    import verde as vd
    return vd.grid_coordinates(region=region, spacing=spacing)


def save_grid(data, longitude, latitude, path: Path, name: str, attrs=None):
    """Save a 2D field as a CF-style NetCDF DataArray (lat/lon) and return it."""
    import xarray as xr
    da = xr.DataArray(
        np.asarray(data),
        coords={"latitude": np.asarray(latitude)[:, 0],
                "longitude": np.asarray(longitude)[0, :]},
        dims=("latitude", "longitude"), name=name, attrs=attrs or {})
    path.parent.mkdir(parents=True, exist_ok=True)
    da.to_netcdf(path)
    return da


def load_grid(path: Path):
    """Load a NetCDF grid saved by save_grid()."""
    import xarray as xr
    return xr.open_dataarray(path)


def project_spacing_m(latitude, spacing_deg=C.SPACING):
    """Approximate (dx, dy) in metres for a geographic grid at a mean latitude.

    Good enough for the FFT transforms over a ~5 deg equatorial box; for a strict
    planar analysis, reproject with project_grid() and read its real spacing.
    """
    deg_m = 111_320.0
    lat0 = float(np.mean(latitude))
    dx = spacing_deg * deg_m * np.cos(np.radians(lat0))
    dy = spacing_deg * deg_m
    return dx, dy


def project_grid(da, epsg=C.PROJ_EPSG):
    """Reproject a lat/lon DataArray to a regular metre grid (EPSG:epsg).

    Returns (values2d, easting1d, northing1d, dx, dy). Requires pyproj + scipy.
    """
    from pyproj import Transformer
    from scipy.interpolate import RegularGridInterpolator

    lon = da["longitude"].values
    lat = da["latitude"].values
    LON, LAT = np.meshgrid(lon, lat)
    tr = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    E, N = tr.transform(LON, LAT)
    e0, e1, n0, n1 = E.min(), E.max(), N.min(), N.max()
    # Target regular grid: median native step in metres.
    dx = np.median(np.diff(E, axis=1))
    dy = np.median(np.diff(N, axis=0))
    east = np.arange(e0, e1, dx)
    north = np.arange(n0, n1, dy)
    EE, NN = np.meshgrid(east, north)
    # Invert back to lon/lat to sample the source grid.
    inv = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
    LO, LA = inv.transform(EE, NN)
    interp = RegularGridInterpolator((lat, lon), da.values,
                                     bounds_error=False, fill_value=np.nan)
    vals = interp(np.column_stack([LA.ravel(), LO.ravel()])).reshape(EE.shape)
    return vals, east, north, dx, dy


# ==========================================================================
# Self-test (pure numpy) — verify the FFT operators against analytic truth
# ==========================================================================
def _selftest() -> int:
    """Verify FFT derivatives / continuation on a periodic analytic field.

    f = sin(a x) cos(b y). Then fx = a cos(a x) cos(b y), fy = -b sin(a x) sin(b y),
    and the first vertical derivative fz = |k| f with k = sqrt(a^2 + b^2).
    """
    n = 256
    L = 1000_000.0                     # 1000 km domain
    dx = dy = L / n
    x = np.arange(n) * dx
    y = np.arange(n) * dy
    X, Y = np.meshgrid(x, y)
    a = 2 * np.pi * 4 / L              # 4 cycles across the domain
    b = 2 * np.pi * 3 / L
    f = np.sin(a * X) * np.cos(b * Y)

    fx = derivative(f, dx, dy, "x", pad_frac=0.0)
    fy = derivative(f, dx, dy, "y", pad_frac=0.0)
    fz = derivative(f, dx, dy, "z", pad_frac=0.0)
    fx_true = a * np.cos(a * X) * np.cos(b * Y)
    fy_true = -b * np.sin(a * X) * np.sin(b * Y)
    fz_true = np.hypot(a, b) * f

    def rel(u, v):
        return np.max(np.abs(u - v)) / np.max(np.abs(v))

    ok = True
    for name, got, true in (("d/dx", fx, fx_true), ("d/dy", fy, fy_true),
                            ("d/dz", fz, fz_true)):
        r = rel(got, true)
        status = "OK" if r < 1e-6 else "FAIL"
        ok &= r < 1e-6
        print(f"  {name}: max rel err {r:.2e}  [{status}]")

    # Upward continuation of a single harmonic scales it by exp(-|k| h).
    h = 20_000.0
    up = upward_continuation(f, dx, dy, h, pad_frac=0.0)
    up_true = np.exp(-np.hypot(a, b) * h) * f
    r = rel(up, up_true)
    status = "OK" if r < 1e-6 else "FAIL"
    ok &= r < 1e-6
    print(f"  upward({h/1e3:.0f} km): max rel err {r:.2e}  [{status}]")

    # Edge detectors: for an isolated symmetric anomaly the THD ridge and the
    # TDR=0 contour should encircle the source. Sanity-check TDR range.
    g = np.exp(-((X - L/2)**2 + (Y - L/2)**2) / (2 * (60_000.0)**2))
    tdr = tilt_derivative(g, dx, dy)
    assert -90.0 <= np.nanmin(tdr) and np.nanmax(tdr) <= 90.0, "TDR out of range"
    print(f"  TDR range: [{np.nanmin(tdr):.1f}, {np.nanmax(tdr):.1f}] deg  [OK]")

    print("SELF-TEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(_selftest())
    print(__doc__)
