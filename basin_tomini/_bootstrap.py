"""
Import bootstrap so the numbered scripts (whose names start with digits and are
therefore not importable as modules) can be run directly, e.g.:

    python basin_tomini/21_bouguer.py

Every script starts with:

    from _bootstrap import C, bu

which puts this folder (and the sibling moho_indonesia folder, for reusing the
tested tesseroid terrain correction) on sys.path and exposes the shared config
(C) and basin utilities (bu).
"""
from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
_MOHO = _HERE.parent / "moho_indonesia"      # reuse moho_utils (tesseroids, I/O)
# Insert _MOHO first, then _HERE, so basin_tomini ends up FIRST on sys.path:
# `config`/`basin_utils` must resolve to THIS folder, not the moho sibling
# (which also has a config.py). moho_utils.py, when reused, then transparently
# picks up basin_tomini's config — whose densities/region we want for Tomini.
for p in (_MOHO, _HERE):
    if str(p) in sys.path:
        sys.path.remove(str(p))
    sys.path.insert(0, str(p))

import config as C          # noqa: E402
import basin_utils as bu    # noqa: E402

__all__ = ["C", "bu"]
