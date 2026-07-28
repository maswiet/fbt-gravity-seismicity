# Panduan Akuisisi Data — Tahap 1

Letakkan semua hasil download ke `data/raw/<nama_dataset>/`. URL dapat berubah; verifikasi sebelum download.

## 1. Sandwell & Smith Marine Gravity (v32.1 atau terbaru)

**Sumber:** https://topex.ucsd.edu/pub/global_grav_1min/
**File yang dibutuhkan:** `grav_32.1.nc` (~1.4 GB, free-air anomaly global 1 arc-min)
**Lisensi:** Open, sitasi Sandwell et al. (2014) Science.

```bash
mkdir -p data/raw/sandwell
cd data/raw/sandwell
wget https://topex.ucsd.edu/pub/global_grav_1min/grav_32.1.nc
# Pendamping topo/bathy untuk koreksi:
wget https://topex.ucsd.edu/pub/global_topo_1min/topo_25.1.nc
```

**Crop ke area studi** (jangan simpan grid global, terlalu besar):
```bash
gmt grdcut grav_32.1.nc -R114/124/-11/-7 -Gsandwell_v32_fbt.nc
gmt grdcut topo_25.1.nc -R114/124/-11/-7 -Gtopo_v25_fbt.nc
```

## 2. ICGEM — XGM2019e_2159 (combined model)

**Sumber:** http://icgem.gfz-potsdam.de/calcgrid
**Cara:** Web form (tidak ada API langsung untuk grid output).

Pengaturan yang harus dipilih:
- **Model:** `XGM2019e_2159`
- **Functional:** `gravity_anomaly_cl` (classical gravity anomaly) ATAU `gravity_disturbance` (lebih tepat secara teori, pilih salah satu dan konsisten)
- **Reference system:** WGS84
- **Height over ellipsoid:** 0 m (untuk anomali permukaan)
- **Tide system:** `tide_free` (standar)
- **Min/max degree:** 2 / 2190 (pakai full resolution)
- **Grid step:** 0.02° (sesuai target resolusi proyek)
- **Latitude limits:** -11 to -7
- **Longitude limits:** 114 to 124
- **Output format:** `gridded data, ASCII xyz` atau `netCDF`

Setelah submit, tunggu email/link download, simpan sebagai:
`data/raw/icgem/xgm2019e_anomaly_fbt.gdf` (atau .nc)

**Alternatif programatis** (lebih canggih, pakai library Harmonica untuk evaluasi koefisien spherical harmonic):
```python
# Lihat scripts/utils.py — fungsi compute_gravity_from_shc()
```

## 3. GGMplus 2013 (untuk validasi resolusi tinggi di darat)

**Sumber:** https://ddfe.curtin.edu.au/models/GGMplus/
**File:** Pilih tile yang mencakup area studi (mis. tile 110E_120E_10S_0S, 120E_130E_10S_0S).
**Resolusi:** 220 m di darat (tidak ada di laut).

Format file: ASCII grid, perlu konversi ke NetCDF:
```bash
# Setelah download, konversi:
gmt xyz2grd ggmplus_tile.dat -R... -I0.0021 -Goutput.nc
```

## 4. DEMNAS dan BATNAS (BIG Indonesia)

**Sumber:** https://tides.big.go.id/DEMNAS/
**Login:** Perlu akun (gratis, registrasi via web).
**Tiles yang dibutuhkan untuk area FBT:**
- DEMNAS (darat, 0.27 arc-detik ≈ 8 m): tiles yang mencakup Bali, Lombok, Sumbawa, Flores, Alor
- BATNAS (laut, 6 arc-detik ≈ 180 m): tiles yang mencakup Laut Bali, Selat Lombok, Laut Flores, Selat Sumba

Setelah download (format .tif), merge dengan rasterio atau gdal:
```bash
gdal_merge.py -o demnas_fbt.tif -of GTiff DEMNAS_*.tif
gdal_merge.py -o batnas_fbt.tif -of GTiff BATNAS_*.tif
```

## 5. GEBCO 2024 (pelengkap batimetri)

**Sumber:** https://www.gebco.net/data_and_products/gridded_bathymetry_data/
**File:** `GEBCO_2024.nc` (sub-grid via web form untuk area studi).
**Resolusi:** 15 arc-detik global.

## 6. Slab2 (Hayes et al. 2018)

**Sumber:** https://www.sciencebase.gov/catalog/item/5aa1b00ee4b0b1c392e86467
**File untuk Sunda:**
- `sun_slab2_dep_02.23.18.grd` — depth to slab top
- `sun_slab2_dip_02.23.18.grd` — dip
- `sun_slab2_str_02.23.18.grd` — strike
- `sun_slab2_thk_02.23.18.grd` — slab thickness

```bash
mkdir -p data/external/slab2
# Download manual semua file Sunda zone, simpan di folder ini
```

## 7. ISC-EHB Bulletin (Seismisitas relokasi)

**Sumber:** http://www.isc.ac.uk/isc-ehb/
**Cara akses:** Web search interface.
**Parameter pencarian:**
- Region: Rectangular: 114° to 124° E, -11° to -7° N
- Date: 1964-01-01 to (latest available)
- Depth: 0–700 km (nanti difilter di script)
- Magnitude: ≥ 3.0 (sesuaikan)
- Output: CSV format

Simpan sebagai: `data/raw/seismicity/isc_ehb_fbt_raw.csv`

**Alternatif programatis via FDSN webservice** (lebih cepat, tapi katalog ISC reviewed bukan EHB relocated):
```python
from obspy.clients.fdsn import Client
client = Client("IRIS")  # atau "USGS", "GFZ"
cat = client.get_events(
    minlatitude=-11, maxlatitude=-7,
    minlongitude=114, maxlongitude=124,
    starttime="1976-01-01", endtime="2025-12-31",
    minmagnitude=3.0
)
cat.write("data/raw/seismicity/iris_fbt.xml", format="QUAKEML")
```

## 8. Global CMT (Fokal mekanisme)

**Sumber:** https://www.globalcmt.org/CMTfiles.html
**File:** Download `jan76_dec20.ndk` + `monthly` updates terbaru.
**Filter ke area studi** dengan script (lihat `03_seismicity_preprocessing.py`).

## 9. Katalog spesifik Lombok 2018 dan tsunami earthquake Flores 1992

Cari supplementary data dari publikasi berikut (biasanya di Zenodo atau journal supplementary):
- Lythgoe et al. (2021), GJI — relokasi aftershock Lombok
- Salman et al. (2020), JGR — coseismic dan postseismic
- Beckers & Lay (1995) — Flores 1992 source

## Sanity check setelah semua data ter-download

Jalankan:
```bash
python scripts/check_data_integrity.py
```

(Script ini akan memverifikasi keberadaan file, range koordinat, dan no-data values.)
