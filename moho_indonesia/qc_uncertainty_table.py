"""qc_uncertainty_table — derive per-station Moho uncertainty for the Bahri (2020)
western-Indonesia RF crustal model from the digitized 1-D Vs(depth) profiles, to
fill the ``Unc'' column left blank in the supplementary QC template.

For each station we pick an objective Moho at a fixed mantle threshold (Vs = 4.3
km/s) and estimate its uncertainty from the transition width (the depth interval
over which Vs rises from 4.0 to 4.5 km/s); sigma = width/2. This is a definition-
consistent, reproducible uncertainty proxy -- NOT a waveform re-inversion.

Third-party (Bahri) data: outputs are written next to the source and are NOT
committed to the public repository. Only this script is tracked.

Run (fbt env):  python moho_indonesia/qc_uncertainty_table.py
"""
from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd

XLSX = pathlib.Path("/Users/maswiet/gmpe-research/outputs/station-velocity-models/"
                    "digitized_data_export/digitized_velocity_models_all_stations.xlsx")
OUT_CSV = XLSX.parent / "station_moho_uncertainty_QC.csv"


def crossing(depth, vs, thr):
    depth, vs = np.asarray(depth), np.asarray(vs)
    for i in range(1, len(vs)):
        if vs[i - 1] < thr <= vs[i]:
            return depth[i - 1] + (thr - vs[i - 1]) / (vs[i] - vs[i - 1]) * (depth[i] - depth[i - 1])
    return np.nan


def main():
    xl = pd.ExcelFile(XLSX)
    vd = xl.parse("Vs_Depth_1km")
    qc = xl.parse("QC_Flags")

    recs = []
    for stn, grp in vd.groupby("station"):
        grp = grp.sort_values("depth_mid_km")
        dep, vs = grp.depth_mid_km.values, grp.vs_km_s.values
        m43 = crossing(dep, vs, 4.3)
        c40, c45 = crossing(dep, vs, 4.0), crossing(dep, vs, 4.5)
        width = c45 - c40 if np.isfinite(c40) and np.isfinite(c45) else np.nan
        sigma = width / 2 if np.isfinite(width) else np.nan
        recs.append((stn, round(m43, 1) if np.isfinite(m43) else np.nan,
                     round(width, 1) if np.isfinite(width) else np.nan,
                     round(sigma, 1) if np.isfinite(sigma) else np.nan,
                     "no clear Vs=4.3 crossing" if not np.isfinite(m43) else ""))
    pick = pd.DataFrame(recs, columns=["station", "moho_vs43_km", "transition_width_km",
                                       "sigma_km", "pick_note"])
    out = qc.merge(pick, on="station", how="left")
    out = out.rename(columns={"moho_depth_km": "moho_tabulated_km"})
    cols = ["no", "station", "longitude", "latitude", "sediment_thickness_km",
            "moho_tabulated_km", "moho_vs_km_s", "moho_vs43_km", "transition_width_km",
            "sigma_km", "qc_status", "qc_notes", "pick_note"]
    out = out[cols]
    out.to_csv(OUT_CSV, index=False)

    print(f"Wrote {OUT_CSV}  ({len(out)} stations)")
    s = out["sigma_km"].dropna()
    print(f"\nPer-station Moho uncertainty (sigma = transition-width/2):")
    print(f"  median sigma = {s.median():.1f} km  (IQR {s.quantile(.25):.1f}-{s.quantile(.75):.1f})")
    print(f"  stations with a clear Vs=4.3 Moho: {out.moho_vs43_km.notna().sum()}/{len(out)} "
          f"({100 * out.moho_vs43_km.notna().mean():.0f}%)")
    print(f"  QC-flagged (Review): {(out.qc_status == 'Review').sum()}/{len(out)}")
    dd = (out.moho_tabulated_km - out.moho_vs43_km).dropna()
    print(f"  tabulated vs objective 4.3-pick: mean|diff| {dd.abs().mean():.1f} km, std {dd.std():.1f} km")


if __name__ == "__main__":
    main()
