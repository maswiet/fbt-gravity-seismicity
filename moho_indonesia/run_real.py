"""
run_real — first REAL end-to-end Moho inversion for Indonesia (coarse).

Uses real public data downloaded via pygmt/GMT and the Bott+Tikhonov tesseroid
inversion. This is a PROOF-OF-PIPELINE run with documented approximations:

  * Gravity      = GMT `earth_faa` (Sandwell/IGPP satellite free-air anomaly),
                   used as a proxy for the gravity disturbance. The exact GOCO5S
                   GGM disturbance (paper) needs a manual ICGEM download.
  * Height       = constant HEIGHT above the ellipsoid (above max topography) so
                   observation points are never inside topographic mass.
  * Sediments    = SKIPPED in v1 (sediment-free Bouguer := Bouguer). Add CRUST1.0
                   (step 13) once its reader is verified.
  * Resolution   = coarse (default 0.5 deg) so the tesseroid forward is fast.

Run (in the fbt env):
    python moho_indonesia/run_real.py --spacing 0.5
"""
from __future__ import annotations

import argparse
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402

import importlib.util as _ilu  # noqa: E402
_spec = _ilu.spec_from_file_location(
    "moho_inversion", pathlib.Path(__file__).with_name("14_moho_inversion.py"))
moho_inversion = _ilu.module_from_spec(_spec)
sys.modules[_spec.name] = moho_inversion          # register so @dataclass resolves
_spec.loader.exec_module(moho_inversion)
_spec16 = _ilu.spec_from_file_location(
    "results16", pathlib.Path(__file__).with_name("16_results_maps.py"))
results16 = _ilu.module_from_spec(_spec16)
sys.modules[_spec16.name] = results16
_spec16.loader.exec_module(results16)

HEIGHT = 4000.0     # m above ellipsoid (above max Indonesia topography ~2.6 km)
Z_REF_KM = 30.0
DRHO = 400.0
MU_REG = 1e-8


def build_grid(spacing):
    w, e, s, n = C.REGION
    lon = np.arange(w, e + 1e-9, spacing)
    lat = np.arange(s, n + 1e-9, spacing)
    return np.meshgrid(lon, lat)


def fetch_data(lon2d, lat2d, resolution, gravity_source):
    """Return (topography, gravity) on the model grid.

    Topography is always GMT earth_relief. Gravity is either the GOCO06S GGM
    disturbance ("ggm", the paper-faithful satellite source) or the GMT earth_faa
    free-air anomaly proxy ("faa").
    """
    import pygmt
    region = list(C.REGION)
    relief = pygmt.datasets.load_earth_relief(resolution=resolution, region=region)
    lon1d, lat1d = lon2d[0, :], lat2d[:, 0]
    topo = relief.interp(lon=lon1d, lat=lat1d).values
    if gravity_source == "ggm":
        import ggm_gravity
        grav = ggm_gravity.fetch_ggm_disturbance(
            lon2d, lat2d, lmax=C.GGM_MAX_DEGREE, height_m=HEIGHT, model=C.GGM_NAME)
    else:
        faa = pygmt.datasets.load_earth_free_air_anomaly(resolution=resolution, region=region)
        grav = faa.interp(lon=lon1d, lat=lat1d).values
    return topo, grav


def main(spacing, resolution, gravity_source):
    C.ensure_dirs()
    tag = "ggm" if gravity_source == "ggm" else "faa"
    src = f"{C.GGM_NAME} GGM disturbance" if gravity_source == "ggm" else "earth_faa proxy"
    lon2d, lat2d = build_grid(spacing)
    print(f"Model grid: {lon2d.shape} at {spacing} deg ({lon2d.size} cells) | gravity = {src}")

    topo, disturbance = fetch_data(lon2d, lat2d, resolution, gravity_source)
    print(f"Real data: topo {topo.min():.0f}..{topo.max():.0f} m | "
          f"gravity {disturbance.min():.0f}..{disturbance.max():.0f} mGal")

    # Bouguer disturbance = faa - topographic/ocean effect (tesseroids).
    tess, dens = mu.topography_to_tesseroids(topo, lon2d, lat2d)
    topo_effect = mu.tesseroid_gravity_grid(tess, dens, lon2d, lat2d, height_m=HEIGHT)
    bouguer = disturbance - topo_effect
    sed_free = bouguer                        # v1: sediments skipped
    print(f"Bouguer disturbance: {bouguer.min():.0f}..{bouguer.max():.0f} mGal")

    # Inversion (explicit forward at the same HEIGHT).
    tess_forward = mu.make_tesseroid_forward(lon2d, lat2d, height_m=HEIGHT)
    def forward_fn(p):                        # noqa: E306
        return tess_forward(p, Z_REF_KM, DRHO)
    result = moho_inversion.invert(sed_free, lon2d, lat2d, drho=DRHO,
                                   z_ref_km=Z_REF_KM, mu_reg=MU_REG,
                                   forward_fn=forward_fn)
    moho = result.moho_depth_km
    print(f"Inversion: {result.n_iterations} iters, final RMS "
          f"{result.misfit_history[-1]:.2f} mGal | "
          f"Moho {moho.min():.1f}..{moho.max():.1f} km")

    mu.save_grid(moho, lon2d, lat2d, C.GRID_MOHO, name="moho_depth",
                 attrs={"units": "km", "spacing_deg": spacing,
                        "note": "v1 coarse: faa proxy, no sediments"})

    # Figures + validation against the real seismic Moho points.
    seismic = mu.load_seismic_moho()
    results16.plot_moho_map(moho, lon2d, lat2d, seismic,
                            out=C.FIGURES / f"real_moho_depth_{tag}.png",
                            title=f"Moho depth (km) — {src}, {spacing}° coarse")
    results16.plot_difference_from_seismic(
        moho, lon2d, lat2d, seismic,
        out=C.FIGURES / f"real_difference_from_seismic_{tag}.png")

    from scipy.interpolate import RegularGridInterpolator
    interp = RegularGridInterpolator((lat2d[:, 0], lon2d[0, :]), moho,
                                     bounds_error=False, fill_value=np.nan)
    est = interp(np.column_stack([seismic.latitude, seismic.longitude]))
    diff = est - seismic.depth_km.values
    ok = np.isfinite(diff)
    print(f"Difference vs {ok.sum()} seismic points: "
          f"mean {np.nanmean(diff[ok]):.2f} km, std {np.nanstd(diff[ok]):.2f} km")
    print("Figures written to", C.FIGURES)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--spacing", type=float, default=0.5)
    ap.add_argument("--resolution", default="30m",
                    help="GMT grid resolution for topography (e.g. 30m, 15m, 10m).")
    ap.add_argument("--gravity", choices=["ggm", "faa"], default="ggm",
                    help="Gravity source: 'ggm' = GOCO06S disturbance (paper-faithful); "
                         "'faa' = earth_faa free-air proxy.")
    args = ap.parse_args()
    main(args.spacing, args.resolution, args.gravity)
