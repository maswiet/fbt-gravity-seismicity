"""Consistency of the gravity Moho with independent published receiver-function
(RF) studies at co-located stations. For each station we plot every published
seismic Moho estimate (they disagree by up to ~20 km) and our gravity value,
showing that the gravity model falls within the seismic spread.

Sources (Moho depth in km): Kieling et al. (2011), Macpherson et al. (2012),
Bora et al. (2016) for Sumatra; Syuhada & Anggono (2016), Anggono et al. (2020)
for West Java; Fauzi et al. (2021, H-kappa) and Bahri (2020, RF inversion) for
the pan-Indonesia compilations.

Run (fbt env):  python moho_indonesia/compare_prior_rf.py
"""
from __future__ import annotations

import pathlib
import sys

import numpy as np
import xarray as xr
from scipy.interpolate import RegularGridInterpolator

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402

# station: (lon, lat, {study: Moho_km})
STN = {
    # --- Sumatra ---
    "GSI":  (97.58, 1.30,  {"Kieling 2011": 40, "Bora 2016": 19, "Fauzi 2021": 20.4, "Bahri 2020": 30}),
    "LHMI": (96.95, 5.23,  {"Macpherson 2012": 19, "Bora 2016": 35, "Fauzi 2021": 38.3, "Bahri 2020": 28}),
    "BKNI": (101.04, 0.33, {"Macpherson 2012": 30, "Fauzi 2021": 30.7, "Bahri 2020": 32}),
    "PSI":  (98.92, 2.69,  {"Kieling 2011": 33, "Bahri 2020": 30}),
    # --- Java ---
    "CGJI": (105.69, -6.61, {"Syuhada 2016": 37.2, "Anggono 2020": 32, "Fauzi 2021": 33.2, "Bahri 2020": 32}),
    "SKJI": (106.56, -7.01, {"Syuhada 2016": 33.6, "Anggono 2020": 30, "Fauzi 2021": 31.0, "Bahri 2020": 22}),
    "CNJI": (107.13, -7.31, {"Syuhada 2016": 35.3, "Fauzi 2021": 30.0, "Bahri 2020": 32}),
    "CISI": (107.82, -7.56, {"Syuhada 2016": 31.9, "Fauzi 2021": 32.8, "Bahri 2020": 34}),
    "CMJI": (108.45, -7.78, {"Syuhada 2016": 34.5, "Anggono 2020": 32, "Fauzi 2021": 40.0, "Bahri 2020": 32}),
}

STUDY_STYLE = {
    "Kieling 2011":   ("#1f77b4", "o"), "Macpherson 2012": ("#2ca02c", "s"),
    "Bora 2016":      ("#9467bd", "^"), "Syuhada 2016":    ("#8c564b", "D"),
    "Anggono 2020":   ("#e377c2", "v"), "Fauzi 2021":      ("#17becf", "P"),
    "Bahri 2020":     ("#7f7f7f", "X"),
}


def main():
    d = xr.open_dataarray(C.GRID_MOHO)
    g = RegularGridInterpolator((d.latitude.values, d.longitude.values), d.values,
                                bounds_error=False, fill_value=np.nan)

    names = list(STN.keys())
    y = np.arange(len(names))[::-1]          # top-to-bottom in listed order
    fig, ax = plt.subplots(figsize=(10, 6))

    seen = set()
    for yi, name in zip(y, names):
        lon, lat, est = STN[name]
        ours = float(g(np.array([[lat, lon]]))[0])
        vals = list(est.values())
        ax.plot([min(vals), max(vals)], [yi, yi], "-", color="0.75", lw=6,
                solid_capstyle="round", zorder=1)          # seismic spread band
        for study, v in est.items():
            c, m = STUDY_STYLE[study]
            ax.scatter(v, yi, c=c, marker=m, s=55, edgecolor="k", lw=0.4, zorder=3,
                       label=study if study not in seen else None)
            seen.add(study)
        ax.scatter(ours, yi, c="#c0392b", marker="*", s=320, edgecolor="k", lw=0.8,
                   zorder=4, label="This study (gravity)" if "ours" not in seen else None)
        seen.add("ours")

    ax.axhline(4.5, color="0.85", lw=0.8)                    # Sumatra | Java divider
    ax.text(15.5, 7.4, "Sumatra", style="italic", color="0.4", fontsize=10)
    ax.text(15.5, 3.4, "Java", style="italic", color="0.4", fontsize=10)
    ax.set_yticks(y); ax.set_yticklabels(names)
    ax.set_xlabel("Moho depth (km)"); ax.set_xlim(14, 43)
    ax.set_title("Gravity Moho vs independent published RF estimates")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=True, fontsize=8.5)
    ax.grid(axis="x", ls=":", color="0.9")
    fig.tight_layout()
    out = C.FIGURES / "prior_rf_consistency.png"
    fig.savefig(out, dpi=170, bbox_inches="tight")

    # console summary
    print("station  ours   seismic range (km)   within range?")
    inside = 0
    for name in names:
        lon, lat, est = STN[name]
        ours = float(g(np.array([[lat, lon]]))[0]); vals = list(est.values())
        ok = min(vals) - 2 <= ours <= max(vals) + 2
        inside += ok
        print(f"{name:5s}  {ours:5.1f}   {min(vals):4.0f}-{max(vals):4.0f}            {'yes' if ok else 'NO'}")
    print(f"within (±2 km of) the seismic spread: {inside}/{len(names)} stations")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
