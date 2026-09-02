"""
Central configuration for the Central Java RF + gravity sediment-thickness study.

Pipeline goal: receiver functions (MERAMEX 2004 teleseismic data) -> Vs layer
inversion (Herrmann CPS rftn96) -> sediment layer thickness per station, then
use those as CONSTRAINTS for a satellite-gravity sediment-thickness inversion.

Public/user data only. Heavy tools: CPS (built) + obspy/rf.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]                 # …/Pak_Zuhdi
DATA_EXTERNAL = ROOT / "data" / "external"
DATA_PROCESSED = ROOT / "data" / "processed" / "rf_java"
FIGURES = ROOT / "figures" / "rf_java"

# --- Inputs ---------------------------------------------------------------
# MERAMEX teleseismic event windows already cut per station/component/DOY.
ARTHA_DIR = Path("/Volumes/Untitled/ARTHA")
MERAMEX_INFO = DATA_EXTERNAL / "meramex" / "INFO.DAT"       # station metadata
GGM_WGM_BOUGUER = DATA_EXTERNAL / "ggm_wgm" / "GGM_WGM_Bouguer_Anomaly.gxf"

# --- Tools ----------------------------------------------------------------
CPS_BIN = Path("/Users/maswiet/Work/CPS330/PROGRAMS.330/bin")

# --- Processed outputs ----------------------------------------------------
STATIONS_CSV = DATA_PROCESSED / "stations.csv"
RF_DIR = DATA_PROCESSED / "rf"                 # per-station receiver functions
VS_DIR = DATA_PROCESSED / "vs_models"          # per-station rftn96 Vs models
SEDIMENT_CSV = DATA_PROCESSED / "sediment_rf.csv"   # RF sediment thickness/station
GRID_SED_GRAV = DATA_PROCESSED / "sediment_thickness_grav.nc"  # final model

# --- Study area (Central Java; refined from station coords in parse step) --
REGION = (109.3, 111.6, -8.4, -6.3)   # (W, E, S, N) land stations span

# --- Receiver-function parameters ----------------------------------------
# Iterative time-domain deconvolution (CPS saciterd / rf package).
RF_SAMPLING = 20.0            # Hz to resample before RF (decimate from 100 Hz)
RF_GAUSS_CRUST = 2.5          # Gaussian width a (~1.2 Hz) for crustal RF
RF_GAUSS_SED = 5.0            # higher a (~2.4 Hz) to resolve shallow sediment
RF_WATERLEVEL = 0.05
RF_ITERATIONS = 200           # iterative deconvolution iterations
P_WIN = (-10.0, 30.0)         # seconds around P for RF window
BP_CORNERS = (0.05, 4.0)      # bandpass (Hz) before deconvolution
MIN_SNR = 2.0                 # SNR gate for keeping an event

# Teleseismic selection (match ARTHA event windows to a global catalog).
DIST_MIN, DIST_MAX = 15.0, 98.0     # degrees
MAG_MIN = 5.0

# --- Vs inversion (rftn96) ------------------------------------------------
# Starting model: sediment over crust over mantle (half-space). Layer Vs (km/s),
# thickness (km). rftn96 perturbs Vs; we read the resulting profile.
START_MODEL_LAYERS = [
    # thickness_km, vp, vs, rho
    (0.5, 2.0, 1.0, 2.1),     # soft sediment
    (1.0, 3.5, 1.9, 2.3),     # consolidated sediment
    (4.0, 5.8, 3.3, 2.7),     # upper crust
    (10.0, 6.2, 3.6, 2.8),    # mid crust
    (15.0, 6.8, 3.9, 2.9),    # lower crust
    (0.0, 8.0, 4.6, 3.3),     # mantle half-space
]
SED_VS_MAX = 2.6              # Vs (km/s) threshold defining "sediment" top layers

# --- Gravity sediment inversion (RF-constrained) --------------------------
RHO_SED = 2300.0             # mean sediment density (kg/m^3)
RHO_BASEMENT = 2670.0        # basement density
SPACING = float(os.environ.get("RFJAVA_SPACING", 0.02))   # deg working grid


def ensure_dirs():
    for p in (DATA_PROCESSED, FIGURES, RF_DIR, VS_DIR):
        p.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    ensure_dirs()
    print("RF-Java config OK")
    print("  ARTHA:", ARTHA_DIR, "exists:", ARTHA_DIR.exists())
    print("  INFO.DAT:", MERAMEX_INFO, "exists:", MERAMEX_INFO.exists())
    print("  CPS rftn96:", (CPS_BIN / "rftn96").exists())
    print("  region:", REGION)
