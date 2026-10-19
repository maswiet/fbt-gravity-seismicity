"""
Rebuild the two-ambient-noise-routes composite (manuscript Fig 11) from the
current panels, so it uses the corrected Spica figures.

Run (fbt):  python ambient_noise/compare_composite.py
"""
import pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIG = ROOT / "figures" / "ambient_noise"

panels = [
    ("rs_fig3_section.png",       "Reflection — autocorrelation (Romero & Schimmel 2018)"),
    ("spica_record_section.png",  "Dispersion — cross-correlation C1 (Spica et al. 2016)"),
    ("basement_map_an.png",       "Product: RF-independent basement depth map"),
    ("spica_dispersion.png",      "Product: Rayleigh group-velocity dispersion"),
]

fig, axes = plt.subplots(2, 2, figsize=(14.5, 13.0))
for ax, (fn, title) in zip(axes.ravel(), panels):
    ax.imshow(mpimg.imread(FIG / fn))
    ax.set_title(title, fontsize=12.5, fontweight="bold", pad=6)
    ax.axis("off")
fig.suptitle("Two seismological-noise routes to the Central Java basin (MERAMEX): "
             "reflection depth vs surface-wave velocity",
             fontsize=15.5, fontweight="bold", y=0.995)
fig.tight_layout(rect=[0, 0, 1, 0.975])
out = FIG / "compare_romero_spica.png"
fig.savefig(out, dpi=170, facecolor="white")
print("Wrote", out)
