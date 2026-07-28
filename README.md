# Flores Back-arc Thrust (FBT) Geometry Study
**Integrasi Gravitasi-Seismisitas untuk Bali–Lombok–Sumbawa–Flores–NTT**

## Struktur Proyek
```
fbt_workflow/
├── README.md                   # File ini
├── environment.yml              # Conda environment
├── 01_data_download_guide.md    # Panduan akuisisi data (manual + script)
├── scripts/
│   ├── 02_gravity_preprocessing.py
│   ├── 03_seismicity_preprocessing.py
│   └── utils.py                 # Helper functions
├── data/
│   ├── raw/                     # Data mentah hasil download
│   ├── processed/               # Output pra-pemrosesan
│   └── external/                # Slab2, peta geologi, dll.
├── notebooks/                   # Eksplorasi interaktif (Jupyter)
└── figures/                     # Output peta dan plot
```

## Area Studi
- Bounding box: **114°–124° BT, 11°–7° LS**
- Proyeksi kerja: UTM zone 50S (EPSG:32750) untuk wilayah barat, atau Mercator/Lambert untuk peta keseluruhan
- Resolusi grid target: **0.02° (~2 km)** untuk regional, **0.005° (~500 m)** untuk fokus area gunung api

## Urutan Eksekusi
1. **Setup environment** (sekali): `conda env create -f environment.yml && conda activate fbt`
2. **Download data** (lihat `01_data_download_guide.md`)
3. **Pra-pemrosesan gravitasi**: `python scripts/02_gravity_preprocessing.py`
4. **Pra-pemrosesan seismisitas**: `python scripts/03_seismicity_preprocessing.py`
5. (Tahap selanjutnya akan ditambahkan)

## Konvensi
- Semua koordinat dalam **WGS84** kecuali dinyatakan lain
- Gravitasi dalam **mGal**, kedalaman dalam **km**, magnitude dalam **Mw**
- Format grid: **NetCDF (.nc)** dengan CF-convention metadata
- Format katalog: **CSV** dengan header standar QuakeML-like
