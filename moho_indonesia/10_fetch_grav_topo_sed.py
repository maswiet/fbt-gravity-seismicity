"""
10 — Acquire input data: satellite gravity, topography, and sediment model.

Replicates the data of Uieda & Barbosa (2017):
  - Satellite gravity : GOCO5S  -> GOCO06s / XGM2019e  (ICGEM calc service)
  - Topography/bathym.: ETOPO1  -> ETOPO 2022 60"       (NOAA NCEI)
  - Sediments         : CRUST1.0 (Laske et al. 2013)    (UCSD)

Downloads use `pooch` and cache into data/raw and data/external. Where automatic
download is not reliable (ICGEM is a queued service), the function prints exact
manual instructions and looks for a file you place yourself.

Requires network access and (for subsetting) xarray. Run inside the `fbt` env.
Run:  python moho_indonesia/10_fetch_grav_topo_sed.py
"""
from __future__ import annotations

import tarfile

from _bootstrap import C, mu  # noqa: F401


# --------------------------------------------------------------------------
# Gravity (ICGEM)
# --------------------------------------------------------------------------
def icgem_request_summary() -> str:
    w, e, s, n = C.REGION_PADDED
    return (
        "ICGEM calculation service — http://icgem.gfz-potsdam.de/calcgrid\n"
        f"  model            : {C.GGM_NAME}\n"
        f"  functional       : gravity_disturbance\n"
        f"  longitude limits : {w} .. {e}\n"
        f"  latitude limits  : {s} .. {n}\n"
        f"  grid step        : {C.SPACING} deg\n"
        f"  height above ell. : {C.COMPUTATION_HEIGHT} m\n"
        f"  max degree       : {C.GGM_MAX_DEGREE}\n"
        f"  tide system      : tide-free (document your choice)\n"
        f"  -> save the resulting .gdf into: {C.GRAVITY_RAW}"
    )


def fetch_gravity() -> None:
    """Stage the ICGEM gravity_disturbance grid (.gdf) into GRAVITY_RAW.

    ICGEM generates grids asynchronously, so this cannot be a simple GET. If no
    .gdf is present, print the exact request parameters for a manual download.
    """
    existing = list(C.GRAVITY_RAW.glob("*.gdf"))
    if existing:
        print("Gravity .gdf already present:", existing[0].name)
        return
    print("No ICGEM .gdf found. Request one with these exact settings:\n")
    print(icgem_request_summary())
    print("\n(Then re-run step 11.)")


# --------------------------------------------------------------------------
# Topography (ETOPO 2022, NOAA NCEI)
# --------------------------------------------------------------------------
ETOPO_URL = (
    "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/"
    "60s_surface_elev_netcdf/ETOPO_2022_v1_60s_N90W180_surface.nc"
)


def fetch_topography() -> None:
    """Download global ETOPO, subset to REGION_PADDED, save topography.nc.

    TODO(verify): confirm the netCDF variable/coord names of the downloaded file
    (commonly z / lat / lon) before trusting the subset.
    """
    import pooch
    import xarray as xr

    out = C.TOPOGRAPHY_RAW / "topography.nc"
    if out.exists():
        print("Topography already present:", out)
        return

    path = pooch.retrieve(ETOPO_URL, known_hash=None,
                          fname="ETOPO_2022_60s.nc", path=str(C.TOPOGRAPHY_RAW))
    ds = xr.open_dataset(path)
    # Normalise coord/var names.
    rename = {}
    for cand in ("lon", "longitude", "x"):
        if cand in ds.coords:
            rename[cand] = "longitude"; break
    for cand in ("lat", "latitude", "y"):
        if cand in ds.coords:
            rename[cand] = "latitude"; break
    ds = ds.rename(rename)
    var = "z" if "z" in ds else list(ds.data_vars)[0]
    w, e, s, n = C.REGION_PADDED
    topo = ds[var].sel(longitude=slice(w, e), latitude=slice(s, n))
    if topo.latitude[0] > topo.latitude[-1]:      # ensure ascending latitude
        topo = topo.sortby("latitude")
    topo.rename("topography").to_netcdf(out)
    print("Wrote", out)


# --------------------------------------------------------------------------
# Sediments (CRUST1.0, UCSD)
# --------------------------------------------------------------------------
CRUST1_URL = "https://igppweb.ucsd.edu/~gabi/crust1/crust1.0.tar.gz"


def fetch_crust1() -> None:
    """Download and unpack CRUST1.0 into CRUST1_DIR."""
    import pooch

    if (C.CRUST1_DIR / "crust1.bnds").exists():
        print("CRUST1.0 already present in", C.CRUST1_DIR)
        return
    archive = pooch.retrieve(CRUST1_URL, known_hash=None,
                             fname="crust1.0.tar.gz", path=str(C.CRUST1_DIR))
    with tarfile.open(archive) as tar:
        tar.extractall(C.CRUST1_DIR)          # noqa: S202 (trusted source)
    print("Unpacked CRUST1.0 into", C.CRUST1_DIR)


def main() -> None:
    C.ensure_dirs()
    fetch_gravity()
    fetch_topography()
    fetch_crust1()
    print("\nRaw inputs staged under", C.DATA_RAW, "and", C.DATA_EXTERNAL)


if __name__ == "__main__":
    main()
