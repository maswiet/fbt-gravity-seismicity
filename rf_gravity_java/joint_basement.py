"""
JOINT basement inversion for Central Java — RF + ambient-noise autocorrelation +
satellite gravity in ONE unified model.

Framework (Uieda & Barbosa 2017 tesseroid + Bott, extended): the residual Bouguer
gravity is fit by a sediment layer whose base is the basement relief b(x,y); the
gravity gives the smooth LATERAL shape between stations, while the two independent
seismological depth datasets pin the ABSOLUTE depth as soft point constraints:

  minimise   ||g(b) - d_grav||^2
           + mu ||R b||^2                          (smoothness)
           + w_rf^2  sum_(RF sites) (b - z_RF)^2    (receiver functions)
           + w_an^2  sum_(AN sites) (b - z_AN)^2    (ambient-noise autocorrelation)

solved with the regularised Bott/Gauss-Newton step. Where RF (deeper) and AN
(shallower) disagree, the joint model takes a weight-balanced compromise; the
dense gravity interpolates between the sparse control points.

Outputs (figures/rf_java/):
  joint_basement_map.png      unified basement-depth map (R&S Fig-8 style, PyGMT)
  joint_scatter.png           joint vs RF, joint vs AN, gravity fit
  joint_section.png           W-E section: RF pts, AN pts, joint basement
  data/processed/rf_java/basement_joint.nc / .csv

Run (fbt):  python rf_gravity_java/joint_basement.py
"""
from __future__ import annotations
import sys, subprocess, pathlib
import numpy as np, pandas as pd, xarray as xr, verde as vd
from scipy import sparse
from scipy.sparse.linalg import spsolve
from scipy.interpolate import RegularGridInterpolator as RGI
from scipy.stats import pearsonr

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import invert_uieda3d as U
from _coast import add_coast

D = U.C.DATA_PROCESSED
FIG = U.C.FIGURES
REGION, SPACING = U.REGION, U.SPACING
ZREF, DRHO = 2500.0, -400.0        # reference level (m), density contrast (kg/m3)
MU = U.MU
WRF, WAN = 45.0, 45.0              # RF / AN constraint weights (x A^2), equal trust
N_ITER = 12


def load_points():
    rf = pd.read_csv(D / "sediment_rf.csv")
    rf = rf[rf.kind.isin(["EDL", "SAM"]) & (rf.h_sed_km > 0)][["lon", "lat", "h_sed_km"]]
    rf = rf.rename(columns={"h_sed_km": "z"})
    an = pd.read_csv(D / "basement_map_an.csv")[["lon", "lat", "depth_km"]].rename(
        columns={"depth_km": "z"})
    return rf, an


def cell_targets(df, latc, lonc, nx):
    col = np.array([int(np.argmin(np.abs(lonc - lo))) for lo in df.lon])
    row = np.array([int(np.argmin(np.abs(latc - la))) for la in df.lat])
    flat = row * nx + col
    cells = {}
    for f_, z_ in zip(flat, df.z.values * 1000.0):
        cells.setdefault(int(f_), []).append(z_)
    idx = np.array(sorted(cells)); z = np.array([np.mean(cells[c]) for c in idx])
    return idx, z


def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    fres = U.residual_gravity()
    lon2d, lat2d = vd.grid_coordinates(REGION, spacing=SPACING)
    dobs = fres(np.stack([lat2d, lon2d], axis=-1))
    latc, lonc = lat2d[:, 0], lon2d[0]
    ny, nx = lon2d.shape
    obs = (lon2d, lat2d, np.full(lon2d.shape, U.R_E))
    A = U.TWO_PI_G * DRHO
    Rm = U.smoothness_operator(ny, nx); RtR = (Rm.T @ Rm).tocsr()
    n = ny * nx

    rf, an = load_points()
    rf_idx, rf_z = cell_targets(rf, latc, lonc, nx)
    an_idx, an_z = cell_targets(an, latc, lonc, nx)
    wrf2, wan2 = WRF * A * A, WAN * A * A
    S = (sparse.csr_matrix((np.full(len(rf_idx), wrf2), (rf_idx, rf_idx)), shape=(n, n)) +
         sparse.csr_matrix((np.full(len(an_idx), wan2), (an_idx, an_idx)), shape=(n, n)))
    LHS = (A * A) * sparse.identity(n, format="csr") + MU * RtR + S
    print(f"grid {lon2d.shape}; RF cells {len(rf_idx)}, AN cells {len(an_idx)}")

    b = np.full(n, ZREF)
    for it in range(N_ITER):
        d = U.forward(lon2d, lat2d, b.reshape(ny, nx), DRHO, ZREF, obs).ravel()
        r = dobs.ravel() - d
        rhs = A * r - MU * (RtR @ (b - ZREF))
        rhs[rf_idx] += wrf2 * (rf_z - b[rf_idx])
        rhs[an_idx] += wan2 * (an_z - b[an_idx])
        b = np.clip(b + spsolve(LHS, rhs), U.B_MIN, U.B_MAX)
    d = U.forward(lon2d, lat2d, b.reshape(ny, nx), DRHO, ZREF, obs)
    grav_rms = float(np.sqrt(np.mean((dobs - d) ** 2)))
    thick = (b / 1000.0).reshape(ny, nx)
    da = xr.DataArray(thick, coords={"lat": latc, "lon": lonc}, dims=["lat", "lon"])
    da.to_netcdf(D / "basement_joint.nc")

    fb = RGI((latc, lonc), thick, bounds_error=False, fill_value=np.nan)
    rf = rf.assign(joint=fb(np.c_[rf.lat, rf.lon])).dropna(subset=["joint"])
    an = an.assign(joint=fb(np.c_[an.lat, an.lon])).dropna(subset=["joint"])
    r_rf = pearsonr(rf.joint, rf.z); r_an = pearsonr(an.joint, an.z)
    print(f"gravity fit RMS {grav_rms:.1f} mGal | joint-vs-RF r={r_rf[0]:+.2f} "
          f"RMS={np.sqrt(np.mean((rf.joint-rf.z)**2)):.2f} km | joint-vs-AN r={r_an[0]:+.2f} "
          f"RMS={np.sqrt(np.mean((an.joint-an.z)**2)):.2f} km")
    # export a joint depth per station-ish grid (for the map, sample at all sites)
    allpts = pd.concat([rf[["lon", "lat"]], an[["lon", "lat"]]]).drop_duplicates()
    allpts = allpts.assign(depth_km=fb(np.c_[allpts.lat, allpts.lon]))
    allpts.dropna().to_csv(D / "basement_joint.csv", index=False)

    # ---- Fig: unified basement map (PyGMT, R&S Fig-8 style) -------------------
    draw_map(thick, latc, lonc, rf, an)

    # ---- Fig: scatters + gravity fit -----------------------------------------
    ext = [lonc.min(), lonc.max(), latc.min(), latc.max()]
    fig = plt.figure(figsize=(15, 4.6)); gs = GridSpec(1, 3, wspace=0.32)
    for gi, (df, name, col) in enumerate([(rf, "RF", "#065A82"), (an, "AN", "#B0512F")]):
        ax = fig.add_subplot(gs[gi])
        ax.scatter(df.z, df.joint, s=26, color=col, edgecolor="white", lw=.3, alpha=.85)
        lim = max(df.z.max(), df.joint.max()) * 1.05
        ax.plot([0, lim], [0, lim], "k--", lw=1)
        rr = pearsonr(df.joint, df.z)[0]; rms = np.sqrt(np.mean((df.joint - df.z) ** 2))
        ax.set_xlabel(f"{name} basement (km)"); ax.set_ylabel("joint basement (km)")
        ax.set_title(f"({'ab'[gi]}) Joint vs {name}", fontweight="bold", fontsize=11)
        ax.text(0.05, 0.95, f"r={rr:+.2f}\nRMS={rms:.1f} km\nn={len(df)}", transform=ax.transAxes,
                va="top", fontsize=10, bbox=dict(boxstyle="round", fc="#FFF3E0", ec="#C98A1A"))
        ax.set_xlim(0, lim); ax.set_ylim(0, lim); ax.grid(alpha=.3)
    ax = fig.add_subplot(gs[2])
    im = ax.imshow(dobs - d, origin="lower", extent=ext, cmap="RdBu_r",
                   vmin=-30, vmax=30, aspect="auto"); add_coast(ax, list(REGION))
    ax.set_title(f"(c) Gravity residual (fit {grav_rms:.0f} mGal)", fontweight="bold", fontsize=11)
    ax.set_xlabel("Lon"); ax.set_ylabel("Lat")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03, label="mGal")
    fig.suptitle("Central Java joint basement inversion (RF + ambient-noise + gravity) — consistency",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94]); fig.savefig(FIG / "joint_scatter.png", dpi=200)
    plt.close(fig); print("Wrote joint_scatter.png")

    # ---- Fig: W-E section -----------------------------------------------------
    lat0 = -7.5; j = int(np.argmin(np.abs(latc - lat0)))
    x = (lonc - lonc.mean()) * 111.32 * np.cos(np.deg2rad(lat0))
    fig, a = plt.subplots(figsize=(12, 4.4))
    a.fill_between(x, thick[j], 0, color="#C8DCE8"); a.plot(x, thick[j], "#10233A", lw=2.4,
                                                            label="joint basement (RF+AN+gravity)")
    for df, c, lab in [(rf, "#065A82", "RF"), (an, "#B0512F", "AN")]:
        near = df[np.abs(df.lat - lat0) < 0.3]
        xr_ = (near.lon.values - lonc.mean()) * 111.32 * np.cos(np.deg2rad(lat0))
        a.scatter(xr_, near.z, c=c, s=40, edgecolor="white", zorder=5, label=lab)
    a.invert_yaxis(); a.set_xlabel("Distance W–E (km)"); a.set_ylabel("basement depth (km)")
    a.set_title(f"Central Java joint basement section at {lat0}°S", fontweight="bold")
    a.legend(); a.grid(alpha=.3); fig.tight_layout()
    fig.savefig(FIG / "joint_section.png", dpi=200); plt.close(fig); print("Wrote joint_section.png")


def draw_map(thick, latc, lonc, rf, an):
    import pygmt
    df = pd.DataFrame({"lon": np.repeat(lonc, len(latc)), "lat": np.tile(latc, len(lonc)),
                       "z": thick.T.ravel()})
    pygmt.config(FONT="12p,Times-Roman", FONT_TITLE="15p,Times-Bold",
                 MAP_FRAME_TYPE="fancy+", MAP_FRAME_PEN="1.4p,black",
                 MAP_FRAME_WIDTH="0.16c", FONT_ANNOT_PRIMARY="10p,Times-Roman")
    fig = pygmt.Figure()
    reg = list(REGION)
    grd = pygmt.surface(x=df.lon, y=df.lat, z=df.z.clip(0.3, 6), spacing=0.02,
                        region=reg, tension=0.35)
    pygmt.makecpt(cmap="turbo", series="0/6/0.5", reverse=True, continuous=False)
    fig.basemap(region=reg, projection="M15c",
                frame=["WSne+tCentral Java unified basement depth (RF + ambient-noise + gravity)",
                       "xa0.5f0.25", "ya0.5f0.25"])
    fig.grdimage(grid=grd, cmap=True, region=reg, projection="M15c")
    fig.coast(region=reg, projection="M15c", resolution="f", shorelines="1/0.6p,black",
              borders=["1/0.3p,gray40"])
    fig.plot(x=rf.lon, y=rf.lat, style="c0.14c", fill="white", pen="0.5p,black",
             region=reg, projection="M15c")
    fig.plot(x=an.lon, y=an.lat, style="t0.20c", fill="black", pen="0.3p,white",
             region=reg, projection="M15c")
    fig.colorbar(frame=["x+lBasement depth", "y+lkm"], position="JBC+o0c/0.9c+w9c/0.4c+h")
    fig.text(x=reg[0] + 0.35, y=reg[3] - 0.12, text="o RF   ^ AN", font="9p,Times-Roman,black",
             justify="TL", region=reg, projection="M15c")
    fig.savefig(str(FIG / "joint_basement_map.png"), dpi=250)
    print("Wrote joint_basement_map.png")


if __name__ == "__main__":
    main()
