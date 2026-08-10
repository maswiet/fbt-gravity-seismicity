"""independent_validation — out-of-sample check of the gravity Moho against
receiver-function depths from five OTHER studies, none used in calibration
(reviewer F1/C5). Reports the pooled bias/RMS and the studies' mutual scatter.

Run (fbt env):  python moho_indonesia/independent_validation.py
"""
from __future__ import annotations

import pathlib
import sys
from collections import defaultdict

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402

# study, station, lon, lat, published Moho depth (km) -- independent of Fauzi (2021)
IND = [
    ("Kieling2011", "PSI", 98.92, 2.69, 33), ("Kieling2011", "GSI", 97.58, 1.30, 40),
    ("Macpherson2012", "BKNI", 101.04, 0.33, 30), ("Macpherson2012", "LHMI", 96.95, 5.23, 19),
    ("Macpherson2012", "MNAI", 102.96, -4.36, 16),
    ("Bora2016", "GSI", 97.58, 1.30, 19), ("Bora2016", "LHMI", 96.95, 5.23, 35),
    ("Syuhada2016", "CGJI", 105.69, -6.61, 37.2), ("Syuhada2016", "CISI", 107.82, -7.56, 31.9),
    ("Syuhada2016", "CMJI", 108.45, -7.78, 34.5), ("Syuhada2016", "CNJI", 107.13, -7.31, 35.3),
    ("Syuhada2016", "SKJI", 106.56, -7.01, 33.6),
    ("Anggono2020", "CGJI", 105.69, -6.61, 32), ("Anggono2020", "CMJI", 108.45, -7.78, 32),
    ("Anggono2020", "SKJI", 106.56, -7.01, 30), ("Anggono2020", "SBJI", 106.13, -6.11, 28),
    ("Anggono2020", "CBJI", 106.93, -6.70, 30), ("Anggono2020", "LEM", 107.62, -6.83, 27),
]


def main():
    d = xr.open_dataarray(C.GRID_MOHO)
    g = RegularGridInterpolator((d.latitude.values, d.longitude.values), d.values,
                                bounds_error=False, fill_value=np.nan)
    om = np.array([float(g(np.array([[la, lo]]))[0]) for _, _, lo, la, _ in IND])
    pm = np.array([m for *_, m in IND])
    diff = om - pm
    print(f"OUR GRAVITY vs INDEPENDENT published RF (N={len(IND)}, 5 studies):")
    print(f"  bias {diff.mean():+.1f}  std {diff.std(ddof=1):.1f}  RMS {np.sqrt((diff**2).mean()):.1f}"
          f"  within +-10 km {100*np.mean(np.abs(diff) <= 10):.0f}%")
    for st in dict.fromkeys(s for s, *_ in IND):
        dd = np.array([o - p for (s, _, lo, la, p), o in zip(IND, om) if s == st])
        print(f"    {st:15s} n={dd.size:2d}  bias {dd.mean():+5.1f}  RMS {np.sqrt((dd**2).mean()):4.1f}")
    byst = defaultdict(list)
    for s, stn, lo, la, m in IND:
        byst[stn].append(m)
    multi = [v for v in byst.values() if len(v) > 1]
    sc = np.concatenate([np.abs(np.array(v) - np.mean(v)) for v in multi])
    print(f"  inter-study scatter at co-located stations: {sc.mean():.1f} km "
          f"(mean |dev from station mean|, {len(multi)} stations)")


if __name__ == "__main__":
    main()
