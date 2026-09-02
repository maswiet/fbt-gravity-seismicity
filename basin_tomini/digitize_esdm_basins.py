"""
Digitize sedimentary-basin outlines for the Teluk Tomini window from the OFFICIAL
public ESDM 2022 "Peta Cekungan Sedimen Indonesia" — a scanned 1:5,000,000 sheet
(raster). Output: an APPROXIMATE GeoJSON of basin polygons in WGS84 lon/lat.

Why this is defensible (and its limits):
  * Source is the authoritative public government basin map (ESDM/Badan Geologi
    2022). Projection on the sheet is geographic (plate carree), WGS84.
  * We georeference the scan with 4 city control points (linear/affine fit) and
    trace each basin by COLOR SEGMENTATION (per-basin colour + connected
    component split by the black boundary lines). No polygon is invented.
  * LIMITS: it is a 1:5M sheet traced from a scan; boundaries are approximate to
    ~a few km. Clearly labelled as such on every map. NOT a substitute for a
    licensed vector basin GIS layer if one is available.

Deps (fbt env): rasterio, scipy, shapely, geopandas, numpy.
Run:  python basin_tomini/digitize_esdm_basins.py
"""
from __future__ import annotations

import os

import numpy as np

# --- Path to the 150-dpi render of ESDM page 1 (see README / provenance) ------
# Regenerate from the official ESDM 2022 PDF (user-provided) with:
#   pdftoppm -r 150 -png content-peta-cekungan-sedimen-indonesia-2022.pdf esdm_full150
# then point ESDM_SHEET_PNG at esdm_full150-1.png. The durable output is the
# GeoJSON; this render is only needed to (re)digitize. Control points below are
# calibrated for the 150-dpi render — re-pick them if you change the DPI.
SHEET_PNG = os.environ.get(
    "ESDM_SHEET_PNG",
    "/private/tmp/claude-501/-Users-maswiet-Work-Students-Pak-Zuhdi/"
    "32d8c96a-abb7-4cf9-910c-db2154706df4/scratchpad/esdm_full150-1.png")

# --- Georeference control points: (col_px, row_px, lon, lat) at 150 dpi --------
CONTROL = [
    (4298, 1127, 124.845, 1.474),   # Manado
    (4070, 1253, 123.059, 0.543),   # Gorontalo
    (3653, 1440, 119.870, -0.898),  # Palu
    (4005, 1850, 122.515, -3.973),  # Kendari
]

# --- Basins to trace: (name, number, class, status, seed_lon, seed_lat, margin_deg)
# Seeds are interior points; within a local window (+/- margin) the connected
# component of the seed's colour that contains the seed becomes the polygon.
# margin bounds runaway flooding and is sized to each basin's known extent.
SEEDS = [
    ("Minahasa",  59, "C (fore-arc)",  "unexplored (limited)", 123.20, 0.95, 2.2),
    ("Gorontalo", 60, "A (back-arc)",  "prospective",          121.80, 0.05, 1.9),
    ("Poso",      62, "E (foreland)",  "unexplored (limited)", 120.75, -1.20, 0.8),
    ("Ampana",    63, "E (foreland)",  "unexplored (limited)", 121.45, -0.80, 0.7),
    ("Tomori",    64, "I-E",           "prospective",          122.00, -1.80, 1.0),
    ("Banggai",   65, "I-F",           "producing",            123.30, -1.45, 1.4),
    ("Lariang",   61, "I-E",           "producing",            119.60, -1.55, 1.1),
    ("Taliabu",   95, "I-F",           "discovery",            124.55, -1.75, 1.0),
]
AREA_KM2 = {59: 63266, 60: 54732, 62: 6182, 63: 1990, 64: 10365,
            65: 43391, 61: 27196, 95: 15037}

COLOR_TOL = 55.0        # RGB distance for the per-basin colour mask
DARK_LUM = 55.0         # only true black lines (green/blue fills lum ~80 must survive)
DARK_DILATE = 1         # thicken boundary lines slightly to break thin colour bridges
MIN_AREA_PX = 150       # drop specks
SIMPLIFY_DEG = 0.012    # polygon simplification (~1.3 km)
OUT_NAME = "basins_esdm_tomini.geojson"


def _fit_affine(control):
    """Fit lon,lat = A[col,row,1]. Returns (rasterio Affine px->world, inverse fn)."""
    from affine import Affine
    M = np.array([[c, r, 1.0] for c, r, _, _ in control])
    lon = np.array([lo for *_, lo, _ in control])
    lat = np.array([la for *_, _, la in control])
    (a, b, cc), *_ = np.linalg.lstsq(M, lon, rcond=None)
    (d, e, ff), *_ = np.linalg.lstsq(M, lat, rcond=None)
    fwd = Affine(a, b, cc, d, e, ff)          # (col,row) -> (lon,lat)
    inv = ~fwd                                 # (lon,lat) -> (col,row)
    # Report fit residuals.
    res = []
    for c, r, lo, la in control:
        plo, pla = fwd * (c, r)
        res.append(np.hypot((plo - lo) * 111.0 * np.cos(np.radians(la)),
                            (pla - la) * 111.0))
    print(f"Georef affine residuals (km): "
          f"{', '.join(f'{x:.1f}' for x in res)}  max={max(res):.1f}")
    return fwd, inv


def main():
    import pathlib
    import sys

    import rasterio
    from rasterio.features import shapes
    from affine import Affine
    from scipy import ndimage
    from shapely.geometry import shape
    from shapely.ops import unary_union
    import geopandas as gpd

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import config as C

    fwd, inv = _fit_affine(CONTROL)

    with rasterio.open(SHEET_PNG) as ds:
        img = ds.read()[:3]                    # (3,H,W) RGB
    rgb = np.transpose(img, (1, 2, 0)).astype(float)
    H, W = rgb.shape[:2]
    # Boundary/text mask (dark lines), dilated to break thin colour bridges.
    lum = rgb.mean(axis=2)
    dark = ndimage.binary_dilation(lum < DARK_LUM, iterations=DARK_DILATE)

    records = []
    for name, num, tclass, status, slon, slat, margin in SEEDS:
        col, row = inv * (slon, slat)
        col, row = int(round(col)), int(round(row))
        if not (0 <= row < H and 0 <= col < W):
            print(f"  ! {name}: seed off-sheet, skipped"); continue
        # Local pixel window (+/- margin deg) around the seed to bound flooding.
        c0, r0 = inv * (slon - margin, slat + margin)
        c1, r1 = inv * (slon + margin, slat - margin)
        cmin, cmax = sorted((int(c0), int(c1)))
        rmin, rmax = sorted((int(r0), int(r1)))
        cmin, rmin = max(0, cmin), max(0, rmin)
        cmax, rmax = min(W, cmax), min(H, rmax)
        win = rgb[rmin:rmax, cmin:cmax]
        win_dark = dark[rmin:rmax, cmin:cmax]
        lr, lc = row - rmin, col - cmin        # seed in window coords

        patch = rgb[max(0, row-3):row+4, max(0, col-3):col+4].reshape(-1, 3)
        seed_color = np.median(patch, axis=0)
        mask = (np.linalg.norm(win - seed_color, axis=2) < COLOR_TOL) & (~win_dark)
        lab, _ = ndimage.label(mask)
        cid = lab[lr, lc]
        if cid == 0:
            print(f"  ! {name}: seed not in any colour blob, skipped"); continue
        comp = ndimage.binary_fill_holes(lab == cid)
        area = int(comp.sum())
        if area < MIN_AREA_PX:
            print(f"  ! {name}: component too small ({area}px), skipped"); continue
        # Windowed affine (shift origin to the window's top-left).
        waffine = fwd * Affine.translation(cmin, rmin)
        geoms = [shape(g) for g, v in shapes(comp.astype(np.uint8), mask=comp,
                                             transform=waffine) if v == 1]
        if not geoms:
            print(f"  ! {name}: no polygon extracted, skipped"); continue
        poly = unary_union(geoms).simplify(SIMPLIFY_DEG)
        records.append({
            "name": name, "number": num, "tectonic": tclass, "status": status,
            "area_km2": AREA_KM2.get(num), "geometry": poly,
        })
        cen = poly.centroid
        flag = "  <clip?>" if area > 0.9 * comp.size else ""
        print(f"  {num:>3} {name:<10} {tclass:<14} area~{area}px "
              f"centroid ({cen.x:.2f},{cen.y:.2f}){flag}")

    if not records:
        print("No basins digitized."); return

    gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
    out = C.DATA_EXTERNAL / OUT_NAME
    C.DATA_EXTERNAL.mkdir(parents=True, exist_ok=True)
    gdf.to_file(out, driver="GeoJSON")
    print("Wrote", out, f"({len(gdf)} basins)")

    if "--qc" in sys.argv:
        _qc_plot(gdf, fwd, rgb, C)


def _qc_plot(gdf, fwd, rgb, C):
    """Overlay digitized polygons on the georeferenced ESDM scan for visual QC."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    H, W = rgb.shape[:2]
    lon_tl, lat_tl = fwd * (0, 0)
    lon_br, lat_br = fwd * (W, H)
    extent = [lon_tl, lon_br, lat_br, lat_tl]     # imshow extent (l,r,b,t)
    fig, ax = plt.subplots(figsize=(11, 9))
    ax.imshow(rgb.astype("uint8"), extent=extent, origin="upper")
    for _, r in gdf.iterrows():
        geom = r.geometry
        polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for p in polys:
            x, y = p.exterior.xy
            ax.plot(x, y, "-", lw=2.0, color="black")
            ax.plot(x, y, "-", lw=1.0, color="cyan")
        c = geom.centroid
        ax.text(c.x, c.y, f"{r['number']}", fontsize=9, fontweight="bold",
                ha="center", va="center", color="white")
    w, e, s, n = C.REGION
    ax.add_patch(plt.Rectangle((w, s), e - w, n - s, fill=False,
                               edgecolor="red", lw=2, ls="--"))
    ax.set_xlim(119.3, 125.7); ax.set_ylim(-2.6, 2.2)
    ax.set_title("QC: digitized ESDM basins over the scan (red = study window)")
    out = C.FIGURES / "qc_esdm_digitization.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print("Wrote QC plot", out)


if __name__ == "__main__":
    main()
