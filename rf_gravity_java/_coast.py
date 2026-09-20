"""Lightweight coastline overlay for plain matplotlib lon/lat axes (cartopy 10m)."""
from __future__ import annotations
import numpy as np

_SEGS = {}


def _segments(region):
    key = tuple(np.round(region, 2))
    if key in _SEGS:
        return _SEGS[key]
    import cartopy.feature as cf
    from shapely.geometry import box
    w, e, s, n = region
    clip = box(w - 0.2, s - 0.2, e + 0.2, n + 0.2)
    segs = []
    for geom in cf.NaturalEarthFeature("physical", "coastline", "10m").geometries():
        if not geom.intersects(clip):
            continue
        g = geom.intersection(clip)
        parts = getattr(g, "geoms", [g])
        for p in parts:
            if p.is_empty or not hasattr(p, "xy"):
                continue
            x, y = p.xy
            segs.append((np.asarray(x), np.asarray(y)))
    _SEGS[key] = segs
    return segs


def add_coast(ax, region, color="k", lw=0.7, z=6, set_aspect=True):
    """Draw GSHHG/Natural-Earth coastline on a lon/lat axes and fix the map aspect.

    set_aspect uses 1/cos(mid-latitude) so 1 km E-W and 1 km N-S plot equal
    (no horizontal stretching)."""
    for x, y in _segments(region):
        ax.plot(x, y, color=color, lw=lw, zorder=z)
    ax.set_xlim(region[0], region[1])
    ax.set_ylim(region[2], region[3])
    if set_aspect:
        midlat = 0.5 * (region[2] + region[3])
        ax.set_aspect(1.0 / np.cos(np.deg2rad(midlat)))
