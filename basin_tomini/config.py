"""
Central configuration for the Teluk Tomini / Gorontalo Basin
satellite-gravity basin-delineation pipeline.

Objective (this project): DELINEATION & STRUCTURAL FRAMEWORK of a frontier
Eastern-Indonesia basin from public satellite gravity — Bouguer anomaly,
regional-residual separation, and edge-detection (derivative-based) maps.
This does NOT invert for depth-to-basement; it maps sub-basins, depocentres,
structural highs, and fault/lineament trends qualitatively.

Public data only (no field acquisition). Heavy geophysics work reuses the
tested tesseroid terrain correction from ../moho_indonesia (moho_utils.py).

Everything the pipeline needs to know about *where* things are and *what*
parameters to use lives here, so the numbered scripts stay thin.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np


def _envf(name, default):
    """Read a float override from the environment (for quick coarse/full runs)."""
    val = os.environ.get(name)
    return float(val) if val not in (None, "") else default

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
# Project root = parent of this file's folder (…/Pak_Zuhdi)
ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = ROOT / "data" / "raw"
DATA_EXTERNAL = ROOT / "data" / "external"
DATA_PROCESSED = ROOT / "data" / "processed" / "basin"
FIGURES = ROOT / "figures" / "basin"

# Inputs
GRAVITY_RAW = DATA_RAW / "gravity"          # Sandwell / ICGEM grids
TOPOGRAPHY_RAW = DATA_RAW / "topography"    # bathymetry/topography grid

# Compatibility shims: the reused moho_indonesia/moho_utils.py does
# `import config` and references these two paths as default argument values at
# import time (in functions we never call from the basin pipeline). Define them
# here so the shared `config` name satisfies moho_utils too. See _bootstrap.py.
MOHO_SEISMIC = DATA_EXTERNAL / "Depth_Moho.txt"
CRUST1_DIR = DATA_EXTERNAL / "crust1.0"

# Processed intermediate/outputs (NetCDF grids)
GRID_FAA = DATA_PROCESSED / "free_air_anomaly.nc"            # satellite gravity input
GRID_TOPO = DATA_PROCESSED / "topography.nc"                 # bathy/topo on model grid
GRID_TERRAIN_EFFECT = DATA_PROCESSED / "terrain_effect.nc"   # tesseroid terrain gravity
GRID_BOUGUER = DATA_PROCESSED / "bouguer_anomaly.nc"         # complete Bouguer
GRID_REGIONAL = DATA_PROCESSED / "bouguer_regional.nc"
GRID_RESIDUAL = DATA_PROCESSED / "bouguer_residual.nc"       # main interpretation field
# Edge-detection derivatives (all derived from the residual)
GRID_THD = DATA_PROCESSED / "total_horizontal_derivative.nc"
GRID_TDR = DATA_PROCESSED / "tilt_derivative.nc"
GRID_ASA = DATA_PROCESSED / "analytic_signal.nc"
GRID_THETA = DATA_PROCESSED / "theta_map.nc"

# --------------------------------------------------------------------------
# Study area (Teluk Tomini / Gorontalo Basin) — degrees (W, E, S, N)
# --------------------------------------------------------------------------
# Tomini Bay: enclosed by the North arm (Minahasa/Gorontalo, N), the East arm
# (SE Sulawesi, S) and the Central neck (W); opens E to the Molucca Sea. The
# deep marine Gorontalo Basin sits within it.
REGION = (120.0, 125.0, -1.5, 1.5)
# Padded computation region so edge-detection FFTs and the terrain correction
# are clean of wrap-around / edge effects. Trim to REGION for interpretation.
REGION_PADDED = (119.0, 126.0, -2.5, 2.5)

# Model/data grid spacing in degrees. 0.02 deg (~2 km) matches Sandwell & Smith
# 1-arc-min altimetric gravity; XGM2019e combined resolves ~0.05-0.1 deg offshore.
# Override for a coarse "smoke-test" run, e.g.:  BASIN_SPACING=0.05 python ...
SPACING = _envf("BASIN_SPACING", 0.02)

# Projected CRS for the planar FFT transforms (edge detection needs metres).
# Tomini straddles the equator near 123 deg E -> UTM zone 51N.
PROJ_EPSG = 32651              # WGS84 / UTM zone 51N
# Constant height (m above the ellipsoid) at which satellite gravity is
# synthesised / the terrain effect is forward-modelled.
COMPUTATION_HEIGHT = 4_000.0

# --------------------------------------------------------------------------
# Densities (kg/m^3) — Bouguer reduction
# --------------------------------------------------------------------------
RHO_CRUST = 2670.0     # standard Bouguer reduction density (rock)
RHO_WATER = 1030.0     # seawater
RHO_OCEAN_CONTRAST = RHO_WATER - RHO_CRUST   # ~ -1640 (water replaces rock offshore)

# --------------------------------------------------------------------------
# Gravity source
# --------------------------------------------------------------------------
# "sandwell" = Sandwell & Smith marine free-air (offshore backbone; place the
#              cropped grid in GRAVITY_RAW, see 20_fetch_gravity_topo.py).
# "gmt"      = GMT earth_faa 1m free-air proxy (auto-download, no login).
# "ggm"      = XGM2019e/EGM2008 gravity disturbance via pyshtools (ggm_gravity).
GRAVITY_SOURCE = "gmt"
GGM_NAME = "XGM2019E"          # pyshtools.datasets.Earth name (combined, high d/o)
GGM_MAX_DEGREE = 719           # ~ 30 km half-wavelength; raise for finer detail

# --------------------------------------------------------------------------
# Regional-residual separation
# --------------------------------------------------------------------------
# "upward"    = residual = Bouguer - upward_continued(Bouguer, height)
# "polynomial"= residual = Bouguer - low-order 2D polynomial trend
# "gaussian"  = residual = gaussian_highpass(Bouguer, wavelength)
SEPARATION_METHOD = "upward"
UPWARD_HEIGHT_M = 25_000.0     # continuation height ~ regional wavelength cut
POLY_DEGREE = 3
GAUSSIAN_CUT_M = 60_000.0      # cut wavelength for the gaussian filter (m)

# Edge-detection: optional upward continuation applied BEFORE derivatives to
# suppress very-short-wavelength noise (0 = none).
PRE_DERIV_UPWARD_M = 0.0


def ensure_dirs() -> None:
    """Create all output directories if missing."""
    for path in (DATA_RAW, DATA_EXTERNAL, DATA_PROCESSED, FIGURES,
                 GRAVITY_RAW, TOPOGRAPHY_RAW):
        path.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_dirs()
    print("Configuration OK.")
    print("  Study region  :", REGION)
    print("  Padded region :", REGION_PADDED)
    print("  Spacing       :", SPACING, "deg  | proj EPSG:", PROJ_EPSG)
    print("  Gravity source:", GRAVITY_SOURCE, "| separation:", SEPARATION_METHOD)
    print("  Processed dir :", DATA_PROCESSED)
