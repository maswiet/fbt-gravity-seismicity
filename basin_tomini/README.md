# Cekungan Teluk Tomini / Gorontalo — delineasi dari gravity satelit

Studi **delineasi cekungan & kerangka struktur** frontier Indonesia Timur
(Teluk Tomini / Cekungan Gorontalo) dari **data gravity satelit publik saja**.
Tujuannya memetakan **sub-cekungan, depocenter, tinggian struktur, dan tren
sesar/lineamen** secara kualitatif — *bukan* inversi kedalaman basement.

> Catatan penting: gravity satelit memetakan **geometri cekungan** ("wadah"),
> bukan keberadaan hidrokarbon. Hasil di sini adalah kerangka struktur untuk
> menyaring area prospektif, bukan bukti akumulasi migas.

## Area studi (`config.py`)

- Region of interest: **120–125°E, 1.5°S–1.5°N** (Teluk Tomini).
- Padded computation region: 119–126°E, 2.5°S–2.5°N (buffer FFT & koreksi terrain).
- Grid: **0.02° (~2 km)**, sesuai resolusi Sandwell & Smith 1 arc-min.
- Proyeksi planar untuk turunan FFT: **UTM 51N (EPSG:32651)**.

## Pipeline

Script bernomor, dijalankan berurutan. Tiap langkah membaca output NetCDF
langkah sebelumnya di `data/processed/basin/` dan menulis yang berikutnya.

| Script | Tahap | Output |
|---|---|---|
| `config.py` | Konfigurasi terpusat: region, spacing, densitas, path, metode | — |
| `basin_utils.py` | Inti numpy: turunan FFT, edge detector, upward cont., separasi + I/O grid | — |
| `20_fetch_gravity_topo.py` | Ambil gravity satelit (GMT earth_faa / Sandwell / GGM) + batimetri | `free_air_anomaly.nc`, `topography.nc` |
| `21_bouguer.py` | Koreksi terrain tesseroid (reuse `moho_indonesia`) → **Bouguer lengkap** | `bouguer_anomaly.nc` |
| `22_regional_residual.py` | Pemisahan regional–residual (upward/poly/gaussian) | `bouguer_residual.nc` |
| `23_edge_detection.py` | THD, TDR, ASA, theta map dari residual (di grid meter, balik ke lat/lon) | `*_derivative.nc`, dst. |
| `24_maps.py` | Peta publikasi PyGMT (5 panel) dengan garis pantai GSHHG | `figures/basin/tomini_*.png` |
| `digitize_esdm_basins.py` | Digitasi batas cekungan dari scan ESDM 2022 (georef titik-kontrol + segmentasi warna) | `data/external/basins_esdm_tomini.geojson` |
| `25_basin_overlay.py` | Overlay batas cekungan ESDM di atas residual Bouguer | `figures/basin/tomini_residual_basins.png` |

### Overlay batas cekungan (ESDM 2022) — CAVEAT

Sumber batas: **Peta Cekungan Sedimen Indonesia, ESDM 2022** (resmi, publik) —
tersedia hanya sebagai **scan raster 1:5.000.000**, bukan vektor. `digitize_esdm_basins.py`
meng-georeferensi scan dengan 4 titik kontrol kota (residual ~≤2.5 km) lalu
men-*trace* poligon via segmentasi warna. Hasilnya **PENDEKATAN** (±beberapa km);
setiap peta diberi label demikian. Untuk regenerasi:

```bash
pdftoppm -r 150 -png content-peta-cekungan-sedimen-indonesia-2022.pdf esdm_full150
ESDM_SHEET_PNG=esdm_full150-1.png python basin_tomini/digitize_esdm_basins.py --qc
python basin_tomini/25_basin_overlay.py
```

QC visual: `figures/basin/qc_esdm_digitization.png` (poligon di atas scan).
Cekungan di jendela studi yang paling terpercaya: **#59 Minahasa (C, fore-arc)**
dan **#60 Gorontalo (A, back-arc)** — luasnya cocok dgn angka resmi. #64/#65/#95
di tepi/luar jendela terpotong oleh window digitasi; perbesar `margin` di `SEEDS`
bila perlu, atau ganti ke file vektor yang lebih akurat bila tersedia.

Menjalankan (dalam env `fbt`):

```bash
conda activate fbt
python basin_tomini/20_fetch_gravity_topo.py
python basin_tomini/21_bouguer.py
python basin_tomini/22_regional_residual.py
python basin_tomini/23_edge_detection.py
python basin_tomini/24_maps.py
```

## Jalur data alternatif: Bouguer GGM+WGM (500 m) — dari Pak

Selain jalur Sandwell (20–21), tersedia **Bouguer GGM+WGM buatan Pak** (Oasis
Montaj) sebagai grid profesional 500 m — dipakai untuk analisis independen &
pembanding.

- Sumber: Google Drive Pak → `GGM+WGM_Bouguer Anomaly.gxf` (GXF, Geosoft ASCII).
  Format biner `.grd` Geosoft **tidak** terbaca GMT/GDAL; **GXF terbaca GDAL**.
- Reproyeksi + crop (proyeksi asli Web Mercator EPSG:3857 — metadata Geosoft
  menandai "UNKNOWN", **diverifikasi via keselarasan garis pantai**):
  ```bash
  gdalwarp -s_srs EPSG:3857 -t_srs EPSG:4326 -te 119 -2.5 126 2.5 \
    -tr 0.005 0.005 -r bilinear -of GTiff "GGM+WGM_Bouguer Anomaly.gxf" b.tif
  gmt grdconvert b.tif data/external/ggm_wgm/bouguer_ggmwgm_tomini.nc
  ```
- Analisis (regional-residual + edge + overlay cekungan) di resolusi native:
  ```bash
  python basin_tomini/ggmwgm_analysis.py
  # -> figures/basin/tomini_{bouguer,residual_basins,tdr}_ggmwgm.png
  ```
- **Provenance untuk sitasi:** WGM2012 (Bonvalot et al. 2012, BGI/CGMW) + GGM;
  konfirmasi GGM spesifik & parameter reduksi Bouguer yang Pak pakai di Oasis
  Montaj. Hasil GGM+WGM 500 m meng-corroborate delineasi Sandwell dgn detail lebih tinggi.

## Data (publik)

- **Gravity satelit (default):** GMT `earth_faa` 1 arc-min (altimetri Sandwell &
  Smith) — otomatis via PyGMT, tanpa login. Alternatif: grid Sandwell yang
  di-crop manual (`GRAVITY_SOURCE="sandwell"`), atau disturbance XGM2019e via
  pyshtools (`"ggm"`, reuse `moho_indonesia/ggm_gravity.py`).
- **Batimetri/topografi:** GMT `earth_relief` 15 arc-sec.
- Sitasi: Sandwell et al. (2014) *Science*; Tozer et al. (2019) untuk earth_relief.

## Metode edge detection (rujukan)

| Produk | Rumus | Guna | Rujukan |
|---|---|---|---|
| THD | √(f_x²+f_y²) | maksima = tepi/sesar/flank cekungan | Cordell & Grauch (1985) |
| TDR | atan2(f_z, THD) | kontur 0° = tepi, bebas amplitudo | Miller & Singh (1994) |
| ASA | √(f_x²+f_y²+f_z²) | puncak di tepi sumber | Roest et al. (1992) |
| Theta | THD/ASA | penajam tepi ternormalisasi | Wijns et al. (2005) |
| Tilt-depth | jarak kontur TDR ±45° / 2 | estimasi kedalaman kontak | Salem et al. (2007) |

Konvensi: z positif ke atas; turunan vertikal pertama = |k|·F, upward
continuation = exp(−|k|h)·F di domain bilangan gelombang (Blakely 1995).

## Status verifikasi

- **`basin_utils.py` — inti FFT terverifikasi.** Self-test membandingkan
  turunan x/y/z dan upward continuation terhadap solusi analitik (error rel.
  ~1e-14):

  ```bash
  python basin_tomini/basin_utils.py --selftest
  ```

- **`config.py` — OK** (`python basin_tomini/config.py`).
- **`20`–`24` — ditulis, belum dijalankan end-to-end** (perlu env `fbt` +
  unduhan data). Reuse dari `moho_indonesia`: `moho_utils.topography_to_tesseroids`
  / `tesseroid_gravity_grid` untuk koreksi terrain, `ggm_gravity` untuk opsi GGM.

## Yang perlu diverifikasi sebelum dipercaya

- Nama variabel/koordinat grid PyGMT `earth_faa` & `earth_relief` saat di-`interp`.
- Sistem tide & tinggi referensi jika memakai opsi GGM (`ggm`).
- Pilihan `UPWARD_HEIGHT_M` (default 25 km) — kalibrasi terhadap lebar cekungan;
  uji beberapa nilai dan bandingkan peta residual.
- Batas laut/darat: koreksi Bouguer memakai kontras air-batuan; pastikan datum
  batimetri konsisten (sea level, +up).
