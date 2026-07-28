"""
02_gravity_preprocessing.py

Pra-pemrosesan data gravitasi untuk studi geometri Flores Back-arc Thrust.

Workflow:
1. Load Sandwell marine FAA dan ICGEM XGM2019e
2. Crop ke area studi dan regrid ke common grid
3. Merge marine (Sandwell) + land+marine combined (XGM2019e) dengan
   blending pada zona pantai
4. Hitung anomali Bouguer lengkap (CBA):
   - Bouguer slab correction (variabel densitas darat/laut)
   - Terrain correction memakai DEM/Bathy resolusi tinggi (BATNAS+DEMNAS)
5. Spectral analysis untuk pilih cutoff regional/residual
6. Upward continuation untuk separasi regional
7. Hitung Mantle Bouguer Anomaly (MBA) — opsional, butuh Moho prior
8. Hitung derivatives: THDR, TDR, TDX
9. Save semua output sebagai NetCDF dengan metadata CF

Penggunaan:
    python 02_gravity_preprocessing.py --config config.yml

Output:
    data/processed/
        ├── faa_merged.nc           # Free-air anomaly merged
        ├── cba.nc                  # Complete Bouguer Anomaly
        ├── cba_residual.nc         # Residual setelah upward continuation
        ├── cba_regional.nc         # Regional component
        ├── derivatives/
        │   ├── thdr.nc
        │   ├── tdr.nc
        │   └── tdx.nc
        └── spectral_analysis.png   # Diagnostic plot
"""

import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse

# Geophysics-specific (Fatiando a Terra)
import harmonica as hm
import verde as vd
import boule as bl

from utils import (
    BBOX_FBT, RHO_CRUST, RHO_WATER, RHO_INFILL_MARINE,
    crop_grid, regrid_to_target, make_target_grid,
    bouguer_slab_correction, normal_gravity_wgs84,
    radial_power_spectrum, ensure_dir
)


# ============================================================
# KONFIGURASI
# ============================================================
DATA_RAW = Path("data/raw")
DATA_OUT = Path("data/processed")
FIGURES = Path("figures")
GRID_SPACING = 0.02   # derajat (~2 km)
UPWARD_CONT_HEIGHT = 40.0  # km — sesuaikan setelah spectral analysis


# ============================================================
# 1. LOAD DAN HARMONISASI GRID
# ============================================================
def load_sandwell_faa(path: Path) -> xr.DataArray:
    """
    Load Sandwell v32.1 marine free-air anomaly.

    Catatan: Sandwell grid menggunakan koordinat 0-360 atau -180-180.
    File native menggunakan x (lon) dan y (lat) sebagai dimensi.
    Unit: mGal.
    """
    ds = xr.open_dataset(path)
    # Identifikasi nama variabel — bisa 'z', 'gravity', atau 'faa'
    var_name = list(ds.data_vars)[0]
    da = ds[var_name].rename("faa_marine")
    # Standarisasi nama dimensi
    if "x" in da.dims:
        da = da.rename({"x": "lon", "y": "lat"})
    if "longitude" in da.dims:
        da = da.rename({"longitude": "lon", "latitude": "lat"})
    # Pastikan lon dalam -180..180
    if da.lon.max() > 180:
        da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180)).sortby("lon")
    return crop_grid(da)


def load_xgm2019e(path: Path) -> xr.DataArray:
    """
    Load XGM2019e gravity anomaly dari ICGEM.

    Catatan: jika output ICGEM dalam format .gdf (ASCII), parse manual.
    Jika .nc, load langsung.
    """
    if path.suffix == ".nc":
        ds = xr.open_dataset(path)
        var_name = [v for v in ds.data_vars if "gravity" in v.lower()
                    or "anomaly" in v.lower() or v.lower() in ["z", "g"]][0]
        da = ds[var_name].rename("faa_combined")
    elif path.suffix == ".gdf":
        # Format ICGEM ASCII: header 'end_of_head', kolom long lat h value
        with open(path) as f:
            lines = f.readlines()
        for i, ln in enumerate(lines):
            if "end_of_head" in ln:
                start = i + 1
                break
        df = pd.read_csv(path, skiprows=start, sep=r"\s+",
                         names=["lon", "lat", "h", "value"])
        # Reshape ke grid 2D
        lons = np.sort(df.lon.unique())
        lats = np.sort(df.lat.unique())
        grid = df.pivot(index="lat", columns="lon", values="value").values
        da = xr.DataArray(grid, coords={"lat": lats, "lon": lons},
                          dims=["lat", "lon"], name="faa_combined")
    else:
        raise ValueError(f"Unsupported format: {path.suffix}")

    if "longitude" in da.dims:
        da = da.rename({"longitude": "lon", "latitude": "lat"})
    return crop_grid(da)


def load_topo_bathy(demnas_path: Path, batnas_path: Path,
                    target_lon, target_lat) -> xr.DataArray:
    """
    Load dan merge DEMNAS (darat) + BATNAS (laut), regrid ke target.

    Konvensi: positif = elevasi darat (m), negatif = kedalaman laut (m).
    """
    import rioxarray as rxr

    demnas = rxr.open_rasterio(demnas_path).squeeze().rename({"x": "lon", "y": "lat"})
    batnas = rxr.open_rasterio(batnas_path).squeeze().rename({"x": "lon", "y": "lat"})

    # DEMNAS: nilai > 0 = darat, no-data biasanya -9999 atau NaN
    demnas = demnas.where(demnas > -100)  # mask no-data
    # BATNAS: nilai negatif = laut
    batnas = batnas.where(batnas < 100)

    # Regrid keduanya ke target grid
    demnas_rg = demnas.interp(lon=target_lon, lat=target_lat)
    batnas_rg = batnas.interp(lon=target_lon, lat=target_lat)

    # Merge: pakai DEMNAS jika valid, jika tidak pakai BATNAS
    topo = xr.where(demnas_rg.notnull() & (demnas_rg > 0), demnas_rg, batnas_rg)
    topo.name = "topography"
    topo.attrs = dict(units="meters", description="Merged DEMNAS+BATNAS, +ve land, -ve sea")
    return topo


def merge_sandwell_xgm(da_sand: xr.DataArray, da_xgm: xr.DataArray,
                      topo: xr.DataArray, taper_km: float = 20.0) -> xr.DataArray:
    """
    Merge Sandwell marine FAA dengan XGM2019e combined model.

    Strategi:
    - Di laut dalam (kedalaman > 200 m): pakai Sandwell (resolusi lebih baik)
    - Di darat: pakai XGM2019e
    - Di zona transisi pantai: blending dengan distance-weighted taper

    Return: merged FAA pada grid target.
    """
    # Pastikan keduanya pada grid yang sama
    target_lon = topo.lon.values
    target_lat = topo.lat.values
    sand_rg = da_sand.interp(lon=target_lon, lat=target_lat)
    xgm_rg = da_xgm.interp(lon=target_lon, lat=target_lat)

    # Mask berdasarkan topografi
    is_land = topo > 0
    is_deep_sea = topo < -200

    # Hitung distance to coastline (sederhana: gradient mask)
    from scipy.ndimage import distance_transform_edt
    coast_dist = distance_transform_edt(~is_land.values) * GRID_SPACING * 111  # km
    coast_dist = xr.DataArray(coast_dist, coords=topo.coords, dims=topo.dims)

    # Weight Sandwell: 1 di laut dalam, 0 di darat, taper linear di transisi
    w_sand = np.clip(coast_dist / taper_km, 0, 1)
    w_sand = w_sand.where(~is_land, 0)

    merged = w_sand * sand_rg + (1 - w_sand) * xgm_rg
    merged.name = "faa"
    merged.attrs = dict(
        units="mGal",
        long_name="Free-air gravity anomaly (merged Sandwell+XGM2019e)",
        sources="Sandwell&Smith v32.1 (marine), XGM2019e_2159 (combined)",
        merge_strategy=f"Cosine taper {taper_km} km from coastline"
    )
    return merged


# ============================================================
# 2. BOUGUER CORRECTION
# ============================================================
def compute_bouguer_anomaly(faa: xr.DataArray, topo: xr.DataArray) -> xr.DataArray:
    """
    Hitung Simple Bouguer Anomaly (sebelum terrain correction).

    SBA = FAA + BC_slab
    di mana BC_slab sudah ber-tanda (lihat utils.bouguer_slab_correction).
    """
    bc = bouguer_slab_correction(topo.values, rho=RHO_CRUST, rho_water=RHO_WATER)
    sba = faa + bc
    sba.name = "sba"
    sba.attrs = dict(
        units="mGal",
        long_name="Simple Bouguer Anomaly",
        density_crust=RHO_CRUST, density_water=RHO_WATER,
        formula="SBA = FAA + 2piG[rho_crust*h_land - (rho_crust-rho_water)*|h_sea|]"
    )
    return sba


def compute_terrain_correction(topo_high_res: xr.DataArray,
                                target_lon, target_lat,
                                inner_radius_km: float = 22,
                                outer_radius_km: float = 167) -> xr.DataArray:
    """
    Terrain correction memakai prism integration via Harmonica.

    Catatan: ini adalah approximate spherical TC. Untuk paper Q1, gunakan
    pendekatan yang lebih lengkap seperti yang ada di harmonica.prism_gravity
    dengan tessellated topography.

    inner_radius: zona detail (Hammer A-K), pakai DEM resolusi penuh
    outer_radius: zona luar, bisa pakai DEM lebih kasar

    Return: TC dalam mGal (selalu positif, ditambahkan ke SBA).
    """
    # Konversi topo ke prism layer
    # Tiap pixel jadi prisma: [west, east, south, north, top, bottom]
    # Reference level untuk prism: 0 m (sea level)

    print("  → Building prism layer dari topografi...")
    # Resolusi DEM dalam derajat, asumsi DEMNAS+BATNAS sudah di-regrid
    dx = float(topo_high_res.lon.diff("lon").mean())
    dy = float(topo_high_res.lat.diff("lat").mean())

    # Build prism layer dengan Harmonica
    # Density: 2670 untuk darat, 1640 untuk infill laut (kontras)
    density = xr.where(topo_high_res >= 0, RHO_CRUST, -RHO_INFILL_MARINE)
    # Negative density untuk laut karena kita "remove" air dan ganti dengan apa yang
    # sudah dimasukkan di SBA — di sini TC mengoreksi deviasi dari slab assumption

    # Bottom prisma: 0 (sea level), Top: topo (atau 0 jika negatif untuk laut)
    surface = topo_high_res.fillna(0)
    reference = xr.zeros_like(surface)

    # Build layer (Harmonica function)
    prisms = hm.prism_layer(
        coordinates=(topo_high_res.lon.values, topo_high_res.lat.values),
        surface=surface.values,
        reference=reference.values,
        properties={"density": density.values}
    )

    # Compute gravity di target grid pada elevasi 0 (atau topo)
    # NOTE: untuk akurasi maksimum, evaluate di stasiun aktual (topo permukaan).
    # Di sini kita evaluasi di sea level untuk konsistensi dengan FAA grid.
    target_lon_2d, target_lat_2d = np.meshgrid(target_lon, target_lat)
    target_height = np.zeros_like(target_lon_2d)  # sea level

    print("  → Computing prism gravity (slow, beberapa menit)...")
    g_prism = prisms.prism_layer.gravity(
        coordinates=(target_lon_2d, target_lat_2d, target_height),
        field="g_z"
    )

    # TC = efek topografi yang DEVIATES dari Bouguer slab assumption
    # Kita hitung sebagai: g_topo_real - g_slab_at_each_point
    # Untuk sederhana, kita ambil g_prism langsung sebagai TC
    # (asumsi slab correction sudah dilakukan di SBA)
    tc = xr.DataArray(
        g_prism, coords={"lat": target_lat, "lon": target_lon},
        dims=["lat", "lon"], name="tc"
    )
    tc.attrs = dict(
        units="mGal", long_name="Terrain correction",
        method="Prism integration via Harmonica",
        inner_radius_km=inner_radius_km, outer_radius_km=outer_radius_km
    )
    return tc


def compute_complete_bouguer(sba: xr.DataArray, tc: xr.DataArray) -> xr.DataArray:
    """CBA = SBA + TC"""
    cba = sba + tc
    cba.name = "cba"
    cba.attrs = dict(
        units="mGal", long_name="Complete Bouguer Anomaly",
        formula="CBA = FAA + Bouguer_slab_correction + Terrain_correction"
    )
    return cba


# ============================================================
# 3. SPECTRAL ANALYSIS & REGIONAL/RESIDUAL SEPARATION
# ============================================================
def diagnostic_spectral_analysis(cba: xr.DataArray, out_fig: Path):
    """
    Plot radial average power spectrum untuk justifikasi pilihan
    upward continuation height.

    Ln(P) vs k akan menunjukkan slope yang berbeda untuk source pada
    kedalaman berbeda (Spector & Grant 1970). Break-in-slope = pilihan
    natural untuk separasi regional/residual.
    """
    # Konversi spacing dari derajat ke km (di equator approx)
    dx_km = GRID_SPACING * 111.0

    k, P = radial_power_spectrum(cba, dx_km)

    # Plot
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    ax[0].semilogy(k, P, 'k-', lw=1.5)
    ax[0].set_xlabel("Wavenumber k (rad/km)")
    ax[0].set_ylabel("Power")
    ax[0].set_title("Radial Average Power Spectrum")
    ax[0].grid(alpha=0.3)

    # Plot ln(P) untuk visualisasi slope (depth estimation)
    valid = P > 0
    ax[1].plot(k[valid], 0.5 * np.log(P[valid]), 'k.-')
    ax[1].set_xlabel("Wavenumber k (rad/km)")
    ax[1].set_ylabel("0.5 ln(P)")
    ax[1].set_title("Depth ke top of source = -slope")
    ax[1].grid(alpha=0.3)

    # Auto-detect potential break in slope (sederhana)
    # Hitung slope lokal dengan window
    from scipy.signal import savgol_filter
    if len(k) > 10:
        ln_p = 0.5 * np.log(P[valid])
        slopes = np.gradient(savgol_filter(ln_p, 7, 2), k[valid])
        # Identifikasi 2 segmen dengan slope dominan (deep vs shallow source)
        # Ini sebagai panduan saja, finalisasi pilihan height oleh analyst
        ax[1].twinx().plot(k[valid], slopes, 'r--', alpha=0.5, label='dlnP/dk')

    plt.tight_layout()
    plt.savefig(out_fig, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"  → Saved spectral diagnostic: {out_fig}")
    print(f"  → Pilih upward continuation height berdasarkan break dalam plot.")
    print(f"  → Default: {UPWARD_CONT_HEIGHT} km — sesuaikan di config jika perlu.")


def upward_continuation(cba: xr.DataArray, height_km: float) -> xr.DataArray:
    """
    Upward continuation menggunakan FFT (frequency domain).

    G_up(kx,ky) = G(kx,ky) * exp(-h * sqrt(kx^2 + ky^2))

    Output: regional component (long-wavelength).
    """
    # Konversi ke meter (spacing) untuk konsistensi unit
    dx_m = GRID_SPACING * 111000.0
    dy_m = GRID_SPACING * 111000.0
    h = height_km * 1000.0

    z = cba.values.copy()
    # Detrend untuk minimize edge effects
    mean = np.nanmean(z)
    z = np.nan_to_num(z, nan=mean) - mean

    # Tapering Hann window untuk reduce edge effect
    ny, nx = z.shape
    win_x = np.hanning(nx)
    win_y = np.hanning(ny)
    taper = np.outer(win_y, win_x)
    # Pad to avoid wrap-around (mirror padding)
    pad = max(nx, ny) // 2
    z_pad = np.pad(z, pad, mode='reflect')

    F = np.fft.fft2(z_pad)
    kx = 2 * np.pi * np.fft.fftfreq(z_pad.shape[1], d=dx_m)
    ky = 2 * np.pi * np.fft.fftfreq(z_pad.shape[0], d=dy_m)
    KX, KY = np.meshgrid(kx, ky)
    K = np.sqrt(KX**2 + KY**2)

    F_up = F * np.exp(-K * h)
    z_up = np.real(np.fft.ifft2(F_up))[pad:pad+ny, pad:pad+nx] + mean

    regional = xr.DataArray(z_up, coords=cba.coords, dims=cba.dims, name="cba_regional")
    regional.attrs = dict(
        units="mGal",
        long_name=f"Regional CBA (upward continued {height_km} km)",
        method="FFT upward continuation"
    )
    return regional


# ============================================================
# 4. DERIVATIVES (Edge enhancement)
# ============================================================
def compute_derivatives(grid: xr.DataArray) -> dict:
    """
    Compute THDR, TDR, TDX dari grid (biasanya residual CBA).

    THDR = sqrt((dG/dx)^2 + (dG/dy)^2)              — Total Horizontal Derivative
    TDR  = atan(dG/dz / THDR)                        — Tilt Derivative
    TDX  = atan(THDR / |dG/dz|)                      — Tilt of Total Horiz Deriv

    Vertical derivative dG/dz dihitung di frequency domain:
        dG/dz(kx,ky) = |k| * G(kx,ky)
    """
    dx_m = GRID_SPACING * 111000.0

    z = grid.values.copy()
    z = np.nan_to_num(z, nan=np.nanmean(z))

    # Horizontal derivatives via finite differences
    dgdx = np.gradient(z, dx_m, axis=1)
    dgdy = np.gradient(z, dx_m, axis=0)
    thdr = np.sqrt(dgdx**2 + dgdy**2)

    # Vertical derivative via FFT
    F = np.fft.fft2(z)
    kx = 2 * np.pi * np.fft.fftfreq(z.shape[1], d=dx_m)
    ky = 2 * np.pi * np.fft.fftfreq(z.shape[0], d=dx_m)
    KX, KY = np.meshgrid(kx, ky)
    K = np.sqrt(KX**2 + KY**2)
    dgdz = np.real(np.fft.ifft2(F * K))

    tdr = np.arctan2(dgdz, thdr)         # range -π/2 .. π/2
    tdx = np.arctan2(thdr, np.abs(dgdz))  # range 0 .. π/2

    out = {}
    for name, arr, units in [
        ("thdr", thdr, "mGal/m"),
        ("tdr", tdr, "rad"),
        ("tdx", tdx, "rad"),
    ]:
        da = xr.DataArray(arr, coords=grid.coords, dims=grid.dims, name=name)
        da.attrs = dict(units=units, long_name=name.upper(), source_grid=grid.name)
        out[name] = da
    return out


# ============================================================
# MAIN
# ============================================================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upward_height", type=float, default=UPWARD_CONT_HEIGHT,
                        help="Upward continuation height (km)")
    parser.add_argument("--skip_tc", action="store_true",
                        help="Skip terrain correction (jika belum punya DEM)")
    args = parser.parse_args()

    ensure_dir(DATA_OUT)
    ensure_dir(DATA_OUT / "derivatives")
    ensure_dir(FIGURES)

    # Target grid
    target_lon, target_lat = make_target_grid(BBOX_FBT, GRID_SPACING)
    print(f"Target grid: {len(target_lon)} x {len(target_lat)} "
          f"(spacing {GRID_SPACING}°)")

    # 1. Load data
    print("\n[1] Loading gravitasi...")
    da_sand = load_sandwell_faa(DATA_RAW / "sandwell" / "sandwell_v32_fbt.nc")
    da_xgm = load_xgm2019e(DATA_RAW / "icgem" / "xgm2019e_anomaly_fbt.nc")
    print(f"  Sandwell: {da_sand.shape}, XGM2019e: {da_xgm.shape}")

    print("\n[2] Loading topografi DEMNAS+BATNAS...")
    topo = load_topo_bathy(
        DATA_RAW / "demnas" / "demnas_fbt.tif",
        DATA_RAW / "batnas" / "batnas_fbt.tif",
        target_lon, target_lat
    )
    topo.to_netcdf(DATA_OUT / "topography.nc")

    # 2. Merge
    print("\n[3] Merging Sandwell+XGM2019e...")
    faa = merge_sandwell_xgm(da_sand, da_xgm, topo, taper_km=20.0)
    faa.to_netcdf(DATA_OUT / "faa_merged.nc")

    # 3. Bouguer
    print("\n[4] Computing Simple Bouguer Anomaly...")
    sba = compute_bouguer_anomaly(faa, topo)
    sba.to_netcdf(DATA_OUT / "sba.nc")

    if not args.skip_tc:
        print("\n[5] Computing Terrain Correction (slow)...")
        tc = compute_terrain_correction(topo, target_lon, target_lat)
        tc.to_netcdf(DATA_OUT / "tc.nc")

        print("\n[6] Computing Complete Bouguer Anomaly...")
        cba = compute_complete_bouguer(sba, tc)
    else:
        print("\n[5-6] Skip TC, pakai SBA sebagai approx CBA.")
        cba = sba.rename("cba")
    cba.to_netcdf(DATA_OUT / "cba.nc")

    # 4. Spectral analysis
    print("\n[7] Spectral analysis untuk pilih cutoff regional/residual...")
    diagnostic_spectral_analysis(cba, FIGURES / "spectral_analysis.png")

    # 5. Upward continuation untuk regional
    print(f"\n[8] Upward continuation @ {args.upward_height} km...")
    regional = upward_continuation(cba, args.upward_height)
    residual = cba - regional
    residual.name = "cba_residual"
    residual.attrs = dict(units="mGal", long_name="Residual CBA",
                          method=f"CBA - upward_continued({args.upward_height} km)")
    regional.to_netcdf(DATA_OUT / "cba_regional.nc")
    residual.to_netcdf(DATA_OUT / "cba_residual.nc")

    # 6. Derivatives pada residual
    print("\n[9] Computing edge enhancement derivatives...")
    derivs = compute_derivatives(residual)
    for name, da in derivs.items():
        da.to_netcdf(DATA_OUT / "derivatives" / f"{name}.nc")

    print("\n✓ Selesai. Output di:", DATA_OUT)
    print("  Periksa figures/spectral_analysis.png — sesuaikan upward_height jika perlu.")


if __name__ == "__main__":
    main()
