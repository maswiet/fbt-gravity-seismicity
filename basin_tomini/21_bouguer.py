"""
21 — Complete Bouguer anomaly from the satellite free-air anomaly.

Offshore, the free-air anomaly still carries the gravitational effect of the
water/rock density contrast (bathymetry). We remove the full terrain effect with
a spherical tesseroid model (reusing the TESTED terrain builder from
../moho_indonesia/moho_utils.py), so:

    Bouguer = free_air_anomaly - terrain_effect

where terrain_effect is the g_z of: land columns (rho 2670) above the ellipsoid
and ocean columns filled with the water-rock contrast (~ -1640). This is the
"complete Bouguer anomaly" (a.k.a. topographic-free field) that isolates the
sub-seafloor density structure — the field we interpret for basins.

Requires the fbt env (harmonica/boule). Reads GRID_FAA + GRID_TOPO.
Run:  python basin_tomini/21_bouguer.py
"""
from __future__ import annotations

import numpy as np

from _bootstrap import C, bu

import moho_utils as mu   # reuse tesseroid terrain model (on sys.path)


def main() -> None:
    C.ensure_dirs()
    faa = bu.load_grid(C.GRID_FAA)
    topo = bu.load_grid(C.GRID_TOPO)
    lon = faa["longitude"].values
    lat = faa["latitude"].values
    LON, LAT = np.meshgrid(lon, lat)

    # Defensive: a single NaN topo cell would make EVERY tesseroid-sum NaN.
    topo_vals = bu.fill_nan_nearest(topo.values)
    faa_vals = bu.fill_nan_nearest(faa.values)

    # Terrain (topography + ocean) effect via tesseroids, at the computation
    # height. Land: rho_crust; ocean: (rho_water - rho_crust) contrast.
    tess, dens = mu.topography_to_tesseroids(
        topo_vals, LON, LAT,
        density_land=C.RHO_CRUST, density_water_contrast=C.RHO_OCEAN_CONTRAST)
    terrain = mu.tesseroid_gravity_grid(
        tess, dens, LON, LAT, height_m=C.COMPUTATION_HEIGHT)

    bu.save_grid(terrain, LON, LAT, C.GRID_TERRAIN_EFFECT, "terrain_effect",
                 attrs={"units": "mGal"})
    bouguer = faa_vals - terrain
    bu.save_grid(bouguer, LON, LAT, C.GRID_BOUGUER, "bouguer_anomaly",
                 attrs={"units": "mGal",
                        "definition": "complete Bouguer = FAA - tesseroid terrain effect"})
    print("Wrote", C.GRID_BOUGUER, "| range (mGal):",
          float(np.nanmin(bouguer)), "..", float(np.nanmax(bouguer)))


if __name__ == "__main__":
    main()
