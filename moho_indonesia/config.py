"""
Central configuration for the Indonesia Moho gravity-inversion pipeline.

Replication of:
    Uieda, L. & Barbosa, V.C.F. (2017). Fast nonlinear gravity inversion in
    spherical coordinates with application to the South American Moho.
    Geophysical Journal International, 208(1), 162-176. doi:10.1093/gji/ggw390

Everything the pipeline needs to know about *where* things are and *what*
parameters to use lives here, so the numbered scripts stay thin.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
# Project root = parent of this file's folder (…/Pak_Zuhdi)
ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_EXTERNAL = ROOT / "data" / "external"
DATA_PROCESSED = ROOT / "data" / "processed" / "moho"
FIGURES = ROOT / "figures" / "moho"

# Inputs
GRAVITY_RAW = DATA_RAW / "gravity"          # ICGEM .gdf grids go here
TOPOGRAPHY_RAW = DATA_RAW / "topography"    # ETOPO grid goes here
CRUST1_DIR = DATA_EXTERNAL / "crust1.0"     # CRUST1.0 model files go here
MOHO_SEISMIC = DATA_EXTERNAL / "Depth_Moho.txt"  # validation Moho (STAT LON LAT DEPTH)

# Processed intermediate/outputs (NetCDF grids unless noted)
GRID_DISTURBANCE = DATA_PROCESSED / "gravity_disturbance.nc"
GRID_TOPO_EFFECT = DATA_PROCESSED / "topographic_effect.nc"
GRID_BOUGUER = DATA_PROCESSED / "bouguer_disturbance.nc"
GRID_SED_EFFECT = DATA_PROCESSED / "sediment_effect.nc"
GRID_SED_FREE_BOUGUER = DATA_PROCESSED / "sediment_free_bouguer.nc"   # inversion INPUT
GRID_MOHO = DATA_PROCESSED / "moho_depth.nc"                          # inversion OUTPUT
GRID_GRAVITY_RESIDUAL = DATA_PROCESSED / "gravity_residual.nc"
HYPERPARAMS_JSON = DATA_PROCESSED / "hyperparameters.json"

# --------------------------------------------------------------------------
# Study area (whole Indonesia) — degrees
# --------------------------------------------------------------------------
# Region of interest. Extended south to -15 deg so the Australian margin is clean
# of edge effects and overlaps the AusMoho model (Kennett et al. 2011, lat <= -10)
# for independent validation. Indonesia proper is -11..6; -11..-15 is the overlap.
REGION = (94.0, 141.0, -15.0, 6.0)   # (W, E, S, N)
# Padded computation region to avoid inversion edge effects (buffered ~2 deg).
# Trim results back to REGION for interpretation.
REGION_PADDED = (92.0, 143.0, -17.0, 8.0)

# Model/data grid spacing in degrees (~0.2 deg ≈ 22 km; matched to the
# effective resolution of satellite-only GGMs; paper used 0.4 deg for S. America).
SPACING = 0.2

# Constant geometric height (m, above the WGS84 ellipsoid) at which the GGM
# gravity is synthesised and all effects are forward modelled. TODO: confirm
# against the height convention of the downloaded ICGEM grid.
COMPUTATION_HEIGHT = 10_000.0

# --------------------------------------------------------------------------
# Densities (kg/m^3)
# --------------------------------------------------------------------------
RHO_CRUST = 2670.0     # continental topography reduction density
RHO_WATER = 1030.0     # seawater; ocean reduction contrast = RHO_WATER - RHO_CRUST
RHO_OCEAN_CONTRAST = RHO_WATER - RHO_CRUST   # ≈ -1640 (paper used -1630)

# Anomalous-Moho density contrast (crust vs mantle). A first guess; the final
# value is ESTIMATED in 15_hyperparameters.py by validation against MOHO_SEISMIC.
RHO_MOHO_CONTRAST = 400.0

# --------------------------------------------------------------------------
# Gravity global model (satellite-only, to match the paper's GOCO5S)
# --------------------------------------------------------------------------
# Choose one and document it in the methods section. Fetch the corresponding
# gravity_disturbance grid from the ICGEM calculation service.
GGM_NAME = "GOCO06S"          # pyshtools.datasets.Earth name; alt: "XGM2019E", "EGM2008"
GGM_MAX_DEGREE = 300          # truncation; satellite-only ~ up to d/o 200-300

# --------------------------------------------------------------------------
# Inversion hyperparameters
# --------------------------------------------------------------------------
# Step 1: regularization parameter mu — chosen by hold-out cross-validation.
MU_VALUES = np.logspace(-10, -2, 17)

# Step 2: reference depth z_ref (km) and density contrast drho (kg/m^3) — chosen
# by validation against the seismic Moho points (MOHO_SEISMIC).
ZREF_VALUES = np.arange(20.0, 45.0 + 0.1, 2.5)     # km
DRHO_VALUES = np.arange(200.0, 600.0 + 0.1, 50.0)  # kg/m^3 (to 600 so the optimum sits inside the frame)

# Gauss-Newton / Bott iteration controls.
MAX_ITERATIONS = 50
CONVERGENCE_TOL = 0.1   # stop when misfit change (mGal) falls below this

# Cross-validation: fraction of gravity points held out for testing.
CV_TEST_FRACTION = 0.25
CV_RANDOM_SEED = 42     # fixed for reproducibility


def ensure_dirs() -> None:
    """Create all output directories if missing."""
    for path in (DATA_RAW, DATA_EXTERNAL, DATA_PROCESSED, FIGURES,
                 GRAVITY_RAW, TOPOGRAPHY_RAW, CRUST1_DIR):
        path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_dirs()
    print("Configuration OK. Study region:", REGION)
    print("Padded region:", REGION_PADDED, "| spacing:", SPACING, "deg")
    print("Validation Moho file:", MOHO_SEISMIC, "exists:", MOHO_SEISMIC.exists())
