"""
10 — Acquire input data: satellite gravity, topography, and sediment model.

Replicates the data used by Uieda & Barbosa (2017):
  - Satellite gravity   : GOCO5S  -> here GOCO06s / XGM2019e (ICGEM)
  - Topography/bathym.   : ETOPO1  -> here ETOPO (via ensaio / pooch)
  - Sediments            : CRUST1.0 (Laske et al. 2013)

This script only downloads/stages the raw inputs into data/raw and data/external.
No processing happens here.

Run:  python moho_indonesia/10_fetch_grav_topo_sed.py
"""
from __future__ import annotations

from _bootstrap import C, mu  # noqa: F401


def fetch_gravity() -> None:
    """Download the GGM gravity_disturbance grid from the ICGEM calc service.

    ICGEM 'calculation service' can return a regular grid of gravity_disturbance
    (or gravity) at a constant height as a .gdf file. Request GGM_NAME over
    REGION_PADDED at SPACING and COMPUTATION_HEIGHT, save to GRAVITY_RAW.

    TODO:
      - Either script the ICGEM request or document the manual web request.
      - Save the .gdf into config.GRAVITY_RAW.
      - Note the exact model, max degree, tide system, and height in the header.
    """
    raise NotImplementedError("Fetch/stage the ICGEM gravity grid.")


def fetch_topography() -> None:
    """Download ETOPO topography/bathymetry over REGION_PADDED.

    TODO: use ensaio/pooch or a manual download; save a NetCDF to
    config.TOPOGRAPHY_RAW. Keep bathymetry negative (metres, ref. sea level).
    """
    raise NotImplementedError("Fetch/stage ETOPO topography.")


def fetch_crust1() -> None:
    """Stage the CRUST1.0 model files (bnds + rho layers) into CRUST1_DIR.

    CRUST1.0 is a 1x1 degree global model. We need the sediment layer tops and
    densities (upper/middle/lower) to build the sediment correction in step 13.

    TODO: place CRUST1.0 files in config.CRUST1_DIR and document the source URL.
    """
    raise NotImplementedError("Stage CRUST1.0 files.")


def main() -> None:
    C.ensure_dirs()
    fetch_gravity()
    fetch_topography()
    fetch_crust1()
    print("Raw inputs staged under", C.DATA_RAW, "and", C.DATA_EXTERNAL)


if __name__ == "__main__":
    main()
