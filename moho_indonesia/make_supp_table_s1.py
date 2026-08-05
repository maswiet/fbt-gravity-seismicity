"""Generate Supporting Information Table S1 (the 105-point RF Moho compilation)
as a LaTeX longtable, for the GRL supporting-information document.

Reads the third-party seismic compilation (Depth_Moho.txt) and writes
manuscript/supp_table_s1.tex. That output is gitignored: the raw compilation is
not published to the public repository before its provenance/authorship is
finalised. Add a per-station 'Source' reference before submission.

Run (fbt env):  python moho_indonesia/make_supp_table_s1.py
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402

OUT = C.ROOT / "manuscript" / "supp_table_s1.tex"


def main():
    s = mu.load_seismic_moho()
    lon = s.longitude.values
    lat = s.latitude.values
    dep = s.depth_km.values
    stat = (s["station"].values if "station" in s
            else [f"S{i+1:03d}" for i in range(len(dep))])

    rows = []
    for st, lo, la, dp in sorted(zip(stat, lon, lat, dep), key=lambda r: -r[1]):
        rows.append(f"{st} & {lo:.2f} & {la:.2f} & {dp:.1f} & \\\\")

    body = "\n".join(rows)
    tex = (
        "\\begin{longtable}{lcccl}\n"
        "\\caption{Receiver-function Moho compilation ($N=105$) used for calibration "
        "and validation: station, longitude, latitude, depth below the ellipsoid, "
        "and source. [Add the per-station Source reference before submission.]}\n"
        "\\label{tab:s1}\\\\\n"
        "\\hline\n"
        "Station & Lon ($^{\\circ}$E) & Lat ($^{\\circ}$) & Depth (km) & Source\\\\\n"
        "\\hline\n\\endfirsthead\n"
        "\\hline Station & Lon ($^{\\circ}$E) & Lat ($^{\\circ}$) & Depth (km) & "
        "Source\\\\ \\hline\n\\endhead\n"
        f"{body}\n"
        "\\hline\n\\end{longtable}\n"
    )
    OUT.write_text(tex)
    print(f"Wrote {OUT} ({len(rows)} rows)")


if __name__ == "__main__":
    main()
