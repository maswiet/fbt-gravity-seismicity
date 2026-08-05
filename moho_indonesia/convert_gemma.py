"""Convert GEMMA t6.asc (ESRI ASCII, crust-mantle boundary elevation) to a
NetCDF Moho-depth grid (km, positive down), latitude ascending."""
import pathlib
import sys

import numpy as np
import xarray as xr

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C  # noqa: E402

src = C.DATA_EXTERNAL / "gemma" / "t6.asc"
hdr = {}
with open(src) as f:
    for _ in range(6):
        k, v = f.readline().split()
        hdr[k] = float(v)
ncols, nrows = int(hdr["ncols"]), int(hdr["nrows"])
cell, x0, y0, nod = hdr["cellsize"], hdr["xllcorner"], hdr["yllcorner"], hdr["NODATA_value"]

vals = np.loadtxt(src, skiprows=6).reshape(nrows, ncols)   # row 0 = north
vals = np.where(vals == nod, np.nan, vals)
moho = -vals                                               # elevation -> depth (+down)

lon = x0 + (np.arange(ncols) + 0.5) * cell                 # cell centres, W->E
lat_top_to_bottom = y0 + (nrows - np.arange(nrows) - 0.5) * cell   # N->S
# flip to ascending latitude
lat = lat_top_to_bottom[::-1]
moho = moho[::-1, :]

da = xr.DataArray(moho, coords={"latitude": lat, "longitude": lon},
                  dims=("latitude", "longitude"), name="moho_depth_km")
out = C.DATA_EXTERNAL / "gemma" / "gemma_moho.nc"
da.to_netcdf(out)
sub = da.sel(latitude=slice(-11, 7), longitude=slice(94, 141))
print(f"Wrote {out}")
print(f"Indonesia window: depth min={float(sub.min()):.1f} max={float(sub.max()):.1f} "
      f"mean={float(sub.mean()):.1f} km")
