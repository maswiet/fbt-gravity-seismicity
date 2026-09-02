# Receiver Functions + Satellite Gravity → Sediment Thickness, Central Java

Seismology as a bridge to basin sediment models for frontier hydrocarbon
exploration. Uses the **MERAMEX 2004** temporary broadband/short-period network
(GFZ; 143 stations, Central Java) teleseismic data + public **GGM+WGM** satellite
gravity, and the **Herrmann Computer Programs in Seismology (CPS)** forward-RF
engine (`hrftn96`). Public/experiment data only.

## Pipeline

| Script | Stage | Output |
|---|---|---|
| `config.py` | Paths, region, RF/inversion parameters | — |
| `parse_stations.py` | Parse MERAMEX `INFO.DAT` → station table | `stations.csv` (143 sta) |
| `build_events.py` | Match ARTHA event windows to USGS catalog (baz, rayp) | `events.csv` (7 teleseisms) |
| `compute_rf.py` | Receiver functions: rotate NE→RT + iterative time-domain deconvolution (Ligorria & Ammon = CPS `saciterd`), per station stack | `rf/*_rf.sac` (110 sta) |
| `invert_vs.py` | Sediment thickness from RF Ps-delay move-out; **validated by Herrmann `hrftn96` forward modelling** | `sediment_rf.csv`, `vs_models/*.mod` |
| `rf_gravity_join.py` | Crop GGM+WGM Bouguer to Central Java, regional–residual, **calibrate + tie to RF** → sediment model | `sediment_thickness_grav.nc` |

Run (in the `fbt` conda env, with CPS built at `~/Work/CPS330`):

```bash
python rf_gravity_java/parse_stations.py
python rf_gravity_java/build_events.py
python rf_gravity_java/compute_rf.py
python rf_gravity_java/invert_vs.py
python rf_gravity_java/rf_gravity_join.py
```

## Key results (this run)

- **110 stations** with receiver functions (7 teleseisms, DOY 137–207 of 2004,
  back-azimuths 86–269°); **103** with a resolvable sediment Ps conversion.
- **RF sediment thickness**: median **~2.8 km**, range **0.9–7.2 km** — consistent
  with published Central Java basin depths.
- **hrftn96 forward modelling** reproduces the observed RF for the derived layer
  (see `figures/rf_java/fwd_demo_*.png`).
- **RF–gravity coupling is weak** (r ≈ 0.1): in volcanic Central Java the Bouguer
  field is dominated by the arc/basement density, not thin sediment. **This is the
  point** — satellite gravity alone is ambiguous here; the receiver-function
  sediment thickness is the physical anchor that turns gravity into a calibrated
  basin model.

## Data & provenance

- Seismic: MERAMEX 2004 (GFZ GIPP), GCF event windows (folder `ARTHA`), station
  metadata `INFO.DAT`. Kept LOCAL (gitignored).
- Gravity: GGM+WGM Bouguer (user-provided GXF, from public GGM + WGM2012,
  Bonvalot et al. 2012). Kept LOCAL.
- Tools: CPS (Herrmann), MIT license; ObsPy; `rf` package.

> Caveat: single-station short-period RF Ps picks are scatter-prone; results are a
> reconnaissance sediment map, not a substitute for seismic reflection depth
> conversion. Sediment Vs assumed 1.5 km/s (Vp/Vs 2.0).
