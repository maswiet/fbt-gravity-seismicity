# GJI LaTeX manuscript

Files:
- `moho-indonesia-gji.tex` — the manuscript in Geophysical Journal International format.
- `refs.bib` — BibTeX references.
- Figures are pulled from `../figures/moho/` via `\graphicspath`.

The markdown draft (`moho-indonesia-manuscript-draft.md`) is kept as the readable source.

## How to compile

The manuscript uses the GJI document class (`gji.cls`) and bib style (`gji.bst`),
which are **not** bundled here (journal-specific). Two options:

### Option 1 — Overleaf (easiest)
1. Open Overleaf → New Project → Templates → search **"Geophysical Journal International"**.
2. Replace the template `.tex` with `moho-indonesia-gji.tex`, add `refs.bib`, and
   upload the figures from `figures/moho/` (or adjust `\graphicspath`).
3. Compile (pdfLaTeX). Overleaf already provides `gji.cls`/`gji.bst`.

### Option 2 — local
1. Download `gji.cls` and `gji.bst` from the GJI author guidelines
   (OUP "Preparing your manuscript" → LaTeX template) into this folder.
2. From `manuscript/`:
   ```
   pdflatex moho-indonesia-gji
   bibtex   moho-indonesia-gji
   pdflatex moho-indonesia-gji
   pdflatex moho-indonesia-gji
   ```

If `gji.cls` is unavailable, the header comment in the `.tex` explains a one-line
fallback to `article` for a quick preview.

## Remaining placeholders (search the .tex for `[...]`)
- Corresponding-author email.
- Citation of the seismic-Moho compilation (`Depth_Moho.txt`) + its depth datum.
- Citation of the active-fault dataset ("Pak Wiwit").
- Confirm the Bahri (2023) thesis title/year in `refs.bib`.
- Acknowledgments (funding, data providers).
