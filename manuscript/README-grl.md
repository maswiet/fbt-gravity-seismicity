# GRL submission package

Files for the **Geophysical Research Letters** (AGU) submission of the Indonesia
gravity-Moho study.

| File | Role |
|---|---|
| `moho-indonesia-grl.tex` | Main manuscript (AGU `agujournal2019` class) |
| `moho-indonesia-grl-si.tex` | Supporting Information (`agutexSI2019` class) |
| `refs.bib` | Shared BibTeX (apacite) |
| `../moho_indonesia/make_supp_table_s1.py` | Builds Table S1 (the 105-point RF list) |
| `supp_table_s1.tex` | Generated Table S1 — **gitignored** (third-party data) |

## Length budget (GRL: ≤ 12 publication units)

PU = words/500 + figures + tables. This manuscript: **4 figures + 1 table = 5 PU**,
abstract **144 words** (< 150), body+captions+abstract ≈ **3–4 PU** ⇒ **≈ 8–9 PU
total**, comfortably within 12. Three Key Points, each ≤ 140 characters. Plain
Language Summary included. Everything else (processing chain, hyperparameter
diagnostics, west/east maps, resolution table, full equations, RF table) is in the
Supporting Information.

## Build

The AGU classes (`agujournal2019.cls`, `agutexSI2019.cls`, `apacite`) are supplied
by AGU — download the **AGU LaTeX template** zip or start from the Overleaf
"AGU" gallery (`https://www.overleaf.com/gallery/tagged/agu`). An Overleaf AGU
project transfers straight into the GRL submission system.

Both `.tex` files reference figures as `./figures/NAME.png` (i.e. a `figures/`
folder next to the manuscript). The source figures live in `../figures/moho/`;
copy the ones used into `manuscript/figures/` before compiling
(this folder is gitignored — source of truth stays `figures/moho/`).

```bash
# 0. stage the figures into ./figures next to the .tex
mkdir -p manuscript/figures
cp figures/moho/{moho_full_clean,validation_seismic,scatter_vandermeijde,compare_global_models,processing_chain,hyperparameters,moho_west,moho_east}.png manuscript/figures/
# 1. build the RF Supporting-Information table (reads the local Depth_Moho.txt)
python moho_indonesia/make_supp_table_s1.py     # writes manuscript/supp_table_s1.tex
# 2. compile main + SI (with the real AGU classes on PATH)
cd manuscript
pdflatex moho-indonesia-grl && bibtex moho-indonesia-grl && pdflatex moho-indonesia-grl && pdflatex moho-indonesia-grl
pdflatex moho-indonesia-grl-si && bibtex moho-indonesia-grl-si && pdflatex moho-indonesia-grl-si && pdflatex moho-indonesia-grl-si
```

The main text now shows the key equations as numbered displays: the gravity
disturbance (1), the tesseroid radial attraction (2), the regularised goal
function (3) and the Bott update (4).

Local proof-compiling **without** the AGU classes: replace `\documentclass{agujournal2019}`
with `\documentclass[11pt]{article}` plus stubs for `\journalname`, `\authors`,
`\affiliation`, `\correspondingauthor`, the `keypoints` environment and
`\acknowledgments`, and alias `\let\citeA\citet` (natbib). This is only for
checking cross-references; the AGU classes are required for a faithful PDF.

## Before submission (placeholders to fill)

- **Figure paths**: AGU wants figures referenced by *filename only* (no
  subdirectories). Flatten `../figures/moho/NAME.png` → `NAME.png` and upload each
  figure file separately (they are in `figures/moho/`).
- **Table S1 Source column**: add the per-station reference for each of the 105 RF
  depths, then re-run `make_supp_table_s1.py`.
- **Corresponding-author email**, **Zenodo DOI** (Open Research), **funding /
  station networks / data providers** (Acknowledgments).
- Confirm the **active-fault dataset** citation (used in Figures S3–S4).

## Figures (main = 4)

1. `moho_full_clean.png` — Moho map of Indonesia.
2. `validation_seismic.png` — residual map + histogram.
3. `scatter_vs_seismic.png` — depth–depth vs seismic (this study, CRUST1.0, GEMMA).
4. `compare_global_models.png` — validation points + differences from CRUST1.0/GEMMA.

Supporting Information figures: `processing_chain.png` (S1), `hyperparameters.png`
(S2), `moho_west.png` (S3), `moho_east.png` (S4).
