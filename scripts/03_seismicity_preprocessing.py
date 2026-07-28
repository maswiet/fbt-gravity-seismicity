"""
03_seismicity_preprocessing.py

Pra-pemrosesan katalog seismik untuk integrasi dengan gravitasi.

Workflow:
1. Load ISC-EHB (atau ISC reviewed) — katalog hiposenter relokasi
2. Load Global CMT — katalog fokal mekanisme
3. Filter spasial ke area FBT
4. Filter kedalaman (≤ 60 km untuk seismisitas crustal)
5. Mask seismisitas slab Sunda menggunakan Slab2 geometry
6. Klasifikasi mekanisme: thrust, normal, strike-slip (rake-based)
7. Filter thrust events sebagai kandidat FBT
8. Declustering (Reasenberg atau Gardner-Knopoff)
9. Save catalog terolah dalam CSV dan QuakeML

Output:
    data/processed/
        ├── catalog_isc_filtered.csv       # All events, filtered & declustered
        ├── catalog_crustal.csv            # Crustal events (depth < 60 km, off-slab)
        ├── catalog_thrust.csv             # Thrust mechanisms only
        ├── gcmt_fbt.csv                   # Global CMT subset
        └── seismicity_density.nc          # KDE pada grid yang sama dengan gravitasi
"""

import numpy as np
import pandas as pd
import xarray as xr
from pathlib import Path
from datetime import datetime

from utils import BBOX_FBT, GRID_SPACING, ensure_dir, haversine_km, make_target_grid


DATA_RAW = Path("data/raw")
DATA_OUT = Path("data/processed")
DATA_EXT = Path("data/external")

# Filter parameters
DEPTH_MAX_CRUSTAL = 60.0     # km — atas asthenosphere/below
SLAB_BUFFER_KM = 15.0        # buffer di sekitar slab top untuk masking
MAG_MIN = 3.0                # magnitudo minimum
THRUST_RAKE_MIN = 45.0       # rake threshold (Aki-Richards)
THRUST_RAKE_MAX = 135.0
THRUST_DIP_MAX = 60.0


# ============================================================
# 1. LOAD KATALOG
# ============================================================
def load_isc_ehb(path: Path) -> pd.DataFrame:
    """
    Load ISC-EHB catalog. Expected CSV format dengan kolom:
    EVENTID, AUTHOR, DATE, TIME, LAT, LON, DEPTH, MAG, MAGTYPE, ...

    Format pasti tergantung opsi export ISC. Adjust kolom mapping jika perlu.
    """
    df = pd.read_csv(path, comment='#', low_memory=False)
    # Standardisasi nama kolom (ISC bisa berbeda capitalization)
    rename = {c: c.lower().strip() for c in df.columns}
    df = df.rename(columns=rename)

    # Mapping fleksibel
    col_map = {}
    for c in df.columns:
        if c in ('lat', 'latitude'): col_map[c] = 'lat'
        elif c in ('lon', 'longitude'): col_map[c] = 'lon'
        elif c in ('depth', 'dep'): col_map[c] = 'depth'
        elif c in ('mag', 'magnitude'): col_map[c] = 'mag'
        elif c in ('eventid', 'evid', 'event_id'): col_map[c] = 'eventid'
    df = df.rename(columns=col_map)

    # Parse datetime
    if 'date' in df.columns and 'time' in df.columns:
        df['origin'] = pd.to_datetime(df['date'].astype(str) + ' ' +
                                      df['time'].astype(str), errors='coerce')
    elif 'origin' in df.columns:
        df['origin'] = pd.to_datetime(df['origin'], errors='coerce')

    # Numerik
    for c in ['lat', 'lon', 'depth', 'mag']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    df = df.dropna(subset=['lat', 'lon', 'depth', 'mag', 'origin'])
    print(f"  Loaded {len(df)} ISC events")
    return df


def load_gcmt_ndk(path: Path) -> pd.DataFrame:
    """
    Parse Global CMT NDK format ke DataFrame.

    NDK format: setiap event = 5 baris.
    Reference: https://www.globalcmt.org/CMTfiles.html
    """
    records = []
    with open(path) as f:
        lines = f.readlines()

    for i in range(0, len(lines) - 4, 5):
        try:
            l1 = lines[i]      # Hypocenter
            l3 = lines[i+2]    # Centroid
            l4 = lines[i+3]    # Moment tensor
            l5 = lines[i+4]    # Principal axes & best double couple

            # Line 1: data source, date, time, lat, lon, depth, mb, MS, location
            tokens = l1.split()
            agency = tokens[0]
            date = tokens[1]
            time = tokens[2]
            lat_h = float(tokens[3])
            lon_h = float(tokens[4])
            dep_h = float(tokens[5])

            # Line 3: centroid lat/lon/depth (kolom fixed-width)
            # Format: "CENTROID:  T+/-T  Lat+/-Lat  Lon+/-Lon  Dep+/-Dep  Type"
            parts = l3.split()
            lat_c = float(parts[3])
            lon_c = float(parts[5])
            dep_c = float(parts[7])

            # Line 4: exponent dan komponen tensor
            exp = int(l4.split()[0])

            # Line 5: principal axes + best DC
            # Format: V N P str dip slp str dip slp Mw
            tokens5 = l5.split()
            # Best double couple (dua nodal planes)
            strike1, dip1, rake1 = float(tokens5[-7]), float(tokens5[-6]), float(tokens5[-5])
            strike2, dip2, rake2 = float(tokens5[-4]), float(tokens5[-3]), float(tokens5[-2])
            mw = float(tokens5[-1])  # last token sebenarnya M0 scalar, perlu konversi

            # Mw dari M0: Mw = (2/3) log10(M0) - 10.7  (M0 dalam dyn-cm)
            # M0 = scalar moment dari line 5 token pertama (atau dari line 4)
            try:
                m0_scalar = float(tokens5[0]) * 10**exp
                mw = (2/3) * np.log10(m0_scalar) - 10.7
            except Exception:
                pass

            origin = pd.to_datetime(f"{date} {time}", errors='coerce')

            records.append(dict(
                origin=origin, lat=lat_c, lon=lon_c, depth=dep_c,
                lat_hypo=lat_h, lon_hypo=lon_h, depth_hypo=dep_h,
                mw=mw,
                strike1=strike1, dip1=dip1, rake1=rake1,
                strike2=strike2, dip2=dip2, rake2=rake2,
                agency=agency
            ))
        except Exception as e:
            continue

    df = pd.DataFrame(records).dropna(subset=['origin', 'lat', 'lon'])
    print(f"  Loaded {len(df)} CMT events")
    return df


def load_slab2(path: Path) -> xr.DataArray:
    """Load Slab2 depth grid (Sunda zone)."""
    da = xr.open_dataarray(path)
    if "x" in da.dims:
        da = da.rename({"x": "lon", "y": "lat"})
    # Slab2 depth: negatif ke bawah (m), kita konversi ke positif km
    da = -da / 1000.0
    da.attrs['units'] = 'km (positive down)'
    return da


# ============================================================
# 2. FILTERING
# ============================================================
def filter_by_bbox(df: pd.DataFrame, bbox=BBOX_FBT) -> pd.DataFrame:
    return df[
        (df.lon >= bbox['west']) & (df.lon <= bbox['east']) &
        (df.lat >= bbox['south']) & (df.lat <= bbox['north'])
    ].copy()


def mask_slab_seismicity(df: pd.DataFrame, slab_depth: xr.DataArray,
                          buffer_km: float = SLAB_BUFFER_KM) -> pd.DataFrame:
    """
    Hapus event yang berada di dalam ±buffer dari Slab2 surface.
    Tujuan: isolasi seismisitas crustal (above slab) dari intra-slab.
    """
    # Interpolate slab depth ke lokasi event
    event_slab_depth = slab_depth.interp(
        lon=xr.DataArray(df['lon'].values, dims='ev'),
        lat=xr.DataArray(df['lat'].values, dims='ev')
    ).values

    # Event valid jika:
    # - Tidak ada slab di lokasi (NaN, di luar Slab2 coverage), ATAU
    # - Event lebih dangkal dari (slab_depth - buffer)
    is_above_slab = np.isnan(event_slab_depth) | \
                    (df['depth'].values < (event_slab_depth - buffer_km))
    n_removed = (~is_above_slab).sum()
    print(f"  Removed {n_removed} events near/below slab")
    return df[is_above_slab].copy()


def classify_focal_mechanism(strike, dip, rake) -> str:
    """
    Aki-Richards convention (rake from -180 to 180).
    Thrust: rake near 90° (45° to 135°)
    Normal: rake near -90° (-135° to -45°)
    Strike-slip: rake near 0° or ±180°
    """
    if THRUST_RAKE_MIN <= rake <= THRUST_RAKE_MAX:
        return "thrust"
    elif -THRUST_RAKE_MAX <= rake <= -THRUST_RAKE_MIN:
        return "normal"
    elif (abs(rake) <= 30) or (abs(rake) >= 150):
        return "strike-slip"
    else:
        return "oblique"


def filter_thrust_events(gcmt: pd.DataFrame) -> pd.DataFrame:
    """
    Identifikasi event thrust dari GCMT.
    Strategi: cek SETIDAKNYA SATU dari dua nodal plane konsisten thrust.
    Tambahan: dip ≤ 60° untuk konsistensi dengan FBT (back-arc thrust dangkal).
    """
    rows = []
    for _, ev in gcmt.iterrows():
        np1_class = classify_focal_mechanism(ev.strike1, ev.dip1, ev.rake1)
        np2_class = classify_focal_mechanism(ev.strike2, ev.dip2, ev.rake2)

        is_thrust = (np1_class == "thrust") or (np2_class == "thrust")
        if not is_thrust:
            continue

        # Pilih plane yang konsisten dengan FBT geometry (dip ≤ 60°, dipping S)
        candidate = None
        for plane_id in [1, 2]:
            strike = ev[f'strike{plane_id}']
            dip = ev[f'dip{plane_id}']
            rake = ev[f'rake{plane_id}']
            if (THRUST_RAKE_MIN <= rake <= THRUST_RAKE_MAX) and (dip <= THRUST_DIP_MAX):
                candidate = (strike, dip, rake)
                break

        if candidate:
            ev_dict = ev.to_dict()
            ev_dict.update(dict(
                fbt_strike=candidate[0],
                fbt_dip=candidate[1],
                fbt_rake=candidate[2]
            ))
            rows.append(ev_dict)

    out = pd.DataFrame(rows)
    print(f"  Identified {len(out)} thrust-mechanism events (FBT-candidate)")
    return out


# ============================================================
# 3. DECLUSTERING (Gardner-Knopoff 1974)
# ============================================================
def gardner_knopoff_declustering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Gardner-Knopoff space-time window declustering.

    Window untuk magnitudo M:
        L(M) = 10^(0.1238*M + 0.983) km    (jarak)
        T(M) = 10^(0.032*M + 2.7389) hari   if M >= 6.5
        T(M) = 10^(0.5409*M - 0.547) hari   if M < 6.5
    """
    df = df.sort_values('mag', ascending=False).reset_index(drop=True)
    n = len(df)
    is_mainshock = np.ones(n, dtype=bool)

    for i in range(n):
        if not is_mainshock[i]:
            continue
        M = df.loc[i, 'mag']
        L = 10**(0.1238 * M + 0.983)  # km
        T = (10**(0.032 * M + 2.7389) if M >= 6.5
             else 10**(0.5409 * M - 0.547))  # days

        # Cek kandidat aftershock/foreshock di seluruh katalog
        d_km = haversine_km(df.lon[i], df.lat[i], df.lon, df.lat)
        dt_days = np.abs((df.origin - df.origin[i]).dt.total_seconds() / 86400)

        within = (d_km <= L) & (dt_days <= T) & (df.mag < M)
        is_mainshock[within.values] = False

    out = df[is_mainshock].sort_values('origin').reset_index(drop=True)
    print(f"  Declustered: {n} → {len(out)} mainshocks")
    return out


# ============================================================
# 4. SEISMICITY DENSITY (KDE)
# ============================================================
def seismicity_kde(df: pd.DataFrame, target_lon, target_lat,
                   bandwidth_deg: float = 0.1) -> xr.DataArray:
    """
    2D Kernel Density Estimation seismisitas pada grid target.
    Bandwidth dalam derajat (≈11 km untuk 0.1°).
    """
    from scipy.stats import gaussian_kde
    if len(df) == 0:
        density = np.zeros((len(target_lat), len(target_lon)))
    else:
        xy = np.vstack([df.lon.values, df.lat.values])
        kde = gaussian_kde(xy, bw_method=bandwidth_deg)
        XX, YY = np.meshgrid(target_lon, target_lat)
        positions = np.vstack([XX.ravel(), YY.ravel()])
        density = kde(positions).reshape(XX.shape)

    da = xr.DataArray(
        density, coords={"lat": target_lat, "lon": target_lon},
        dims=["lat", "lon"], name="seismicity_density"
    )
    da.attrs = dict(
        units="events/deg^2 (relative)",
        long_name="2D KDE seismicity density",
        bandwidth_deg=bandwidth_deg, n_events=len(df)
    )
    return da


# ============================================================
# MAIN
# ============================================================
def main():
    ensure_dir(DATA_OUT)

    # 1. Load ISC catalog
    print("[1] Loading ISC-EHB catalog...")
    isc = load_isc_ehb(DATA_RAW / "seismicity" / "isc_ehb_fbt_raw.csv")
    isc = filter_by_bbox(isc)
    isc = isc[isc.mag >= MAG_MIN]
    print(f"  After bbox + Mw>={MAG_MIN}: {len(isc)} events")

    # 2. Load Slab2 dan mask
    print("\n[2] Loading Slab2 dan masking intra-slab events...")
    slab = load_slab2(DATA_EXT / "slab2" / "sun_slab2_dep_02.23.18.grd")
    isc_crust = mask_slab_seismicity(isc, slab, buffer_km=SLAB_BUFFER_KM)
    isc_crust = isc_crust[isc_crust.depth <= DEPTH_MAX_CRUSTAL]
    print(f"  Crustal events: {len(isc_crust)}")

    # 3. Declustering
    print("\n[3] Declustering (Gardner-Knopoff)...")
    isc_decl = gardner_knopoff_declustering(isc_crust)

    # Save filtered ISC
    isc_crust.to_csv(DATA_OUT / "catalog_crustal.csv", index=False)
    isc_decl.to_csv(DATA_OUT / "catalog_crustal_declustered.csv", index=False)

    # 4. Load dan filter GCMT
    print("\n[4] Loading Global CMT...")
    gcmt = load_gcmt_ndk(DATA_RAW / "gcmt" / "jan76_present.ndk")
    gcmt = filter_by_bbox(gcmt)
    gcmt = gcmt[gcmt.depth <= DEPTH_MAX_CRUSTAL]
    print(f"  GCMT in bbox + crustal: {len(gcmt)}")

    # 5. Mask slab pada GCMT juga
    gcmt_crust = mask_slab_seismicity(gcmt, slab, buffer_km=SLAB_BUFFER_KM)

    # 6. Filter thrust mechanisms
    print("\n[5] Filtering thrust mechanisms (FBT-candidate)...")
    thrust = filter_thrust_events(gcmt_crust)
    gcmt_crust.to_csv(DATA_OUT / "gcmt_crustal.csv", index=False)
    thrust.to_csv(DATA_OUT / "catalog_thrust.csv", index=False)

    # 7. KDE pada grid gravitasi
    print("\n[6] Computing seismicity density (KDE)...")
    target_lon, target_lat = make_target_grid(BBOX_FBT, GRID_SPACING)
    density_all = seismicity_kde(isc_decl, target_lon, target_lat, bandwidth_deg=0.1)
    density_thrust = seismicity_kde(thrust, target_lon, target_lat, bandwidth_deg=0.15)

    density_all.to_netcdf(DATA_OUT / "seismicity_density_all.nc")
    density_thrust.to_netcdf(DATA_OUT / "seismicity_density_thrust.nc")

    # 8. Summary
    print("\n=== SUMMARY ===")
    print(f"All ISC events in area:        {len(isc)}")
    print(f"Crustal (depth ≤ {DEPTH_MAX_CRUSTAL}, off-slab): {len(isc_crust)}")
    print(f"After declustering:            {len(isc_decl)}")
    print(f"GCMT in area (crustal):        {len(gcmt_crust)}")
    print(f"FBT-candidate thrust events:   {len(thrust)}")
    print(f"\nOutput: {DATA_OUT}")


if __name__ == "__main__":
    main()
