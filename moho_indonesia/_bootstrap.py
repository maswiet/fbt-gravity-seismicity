"""
Import bootstrap so the numbered scripts (whose names start with digits and are
therefore not importable as modules) can be run directly, e.g.:

    python moho_indonesia/11_gravity_disturbance.py

Every script starts with:

    from _bootstrap import C, mu

which puts this folder on sys.path and exposes the shared config (C) and
utilities (mu).
"""
from __future__ import annotations

import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import config as C          # noqa: E402
import moho_utils as mu     # noqa: E402

__all__ = ["C", "mu"]
