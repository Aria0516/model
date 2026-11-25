"""Exploratory (not pre-specified; asked 2026-11-25): can the PIN1 data show primordia once the radial trend is removed?

Three readouts per L1 cell, each compared with auxin input (-ln qDII, smoothed) after removing the radial trend:
  1. PIN1 level from the walls (own-side PIN1 / PI, area-weighted)      -- as in fig_X1
  2. PIN1 level from the authors' cell table (cell PIN1 / cell PI)      -- independent of the wall extraction
  3. convergence of the tangential part of the efflux field: how much neighbours' efflux points at the cell after the
     radial (global inward) component is removed; the classic PIN1 convergence marker of incipient primordia
Site-centred averages: auxin-input maxima found in the qDII channel of the same meristem (20-50 um), readout averaged in
rings around them, against the same rings around the same sites rotated to random angles at the same radius.

python explore_pin1_level.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi, cKDTree

import pin1_polarity as PP

OUT = Path(__file__).resolve().parent / "out"
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "savefig.dpi": 400,
                     "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False})
W, RMAX = 13.5 / 2.54, 52.0
RINGS = np.arange(0.0, 22.6, 4.5)                    # one cell spacing per ring
BAND = (15.0, 50.0)
N_NULL = 200


def short(name):
    p = name.split("_")
    return f"{p[1]} SAM{int(p[3][3:])}"


def load(f):
    w, cells = PP.load(f)
    l1 = cells[cells.layer == 1].set_index("label")
    cen = PP.centre(l1.reset_index())
    s = PP.sides(w, set(l1.index), True)
    other = s.rename(columns={"cell": "other", "other": "cell", "PIN1": "PIN1_n", "PI": "PI_n"})[["cell", "other", "PIN1_n", "PI_n"]]
    s = s.merge(other, on=["cell", "other"])
    xy = l1[["center_x", "center_y"]]
    e = xy.loc[s.other].values - xy.loc[s.cell].values
    d = np.hypot(e[:, 0], e[:, 1])
    ok = d > 1e-6
    s, e = s[ok], e[ok] / d[ok, None]
    asym = ((s.PIN1 - s.PIN1_n) / (s.PIN1 + s.PIN1_n)).values
    g = pd.DataFrame(dict(cell=s.cell.values, ax=s.area.values * asym * e[:, 0], ay=s.area.values * asym * e[:, 1],
                          a=s.area.values, lev=s.area.values * (s.PIN1 / s.PI).values)).groupby("cell").sum()
    t = pd.DataFrame(dict(vx=g.ax / g.a, vy=g.ay / g.a, wall=np.log(g.lev / g.a)))
    t["cellpin"] = np.log(l1.loc[t.index, "PIN1"].values / l1.loc[t.index, "PI"].values)
    t["qDII"] = l1.loc[t.index, "qDII"].values
    pos = xy.loc[t.index].values - cen
    t["x"], t["y"] = pos[:, 0], pos[:, 1]
    t["r"] = np.hypot(t.x, t.y)
    return t[t.r < RMAX + 6].copy()


def smooth(xy, v, radius):
    tree = cKDTree(xy)
    return np.array([np.nanmedian(v[nb]) for nb in tree.query_ball_point(xy, radius)])


def detrend(r, v, half=3.0):
    """Subtract the running median over cells within +-half um of the same radius."""
    o = np.argsort(r)
    rs, vs = r[o], v[o]
    lo, hi = np.searchsorted(rs, rs - half), np.searchsorted(rs, rs + half, side="right")
    trend = np.array([np.nanmedian(vs[a:b]) for a, b in zip(lo, hi)])
    out = np.empty_like(v)
    out[o] = vs - trend
    return out


def tangential_convergence(t, radius=8.0):
    """For each cell, the mean over neighbours within `radius` of the tangential efflux component pointing at the cell."""
    xy = t[["x", "y"]].values
    r = np.maximum(t.r.values, 1e-9)
    rhat = xy / r[:, None]
    v = t[["vx", "vy"]].values
    vt = v - (v * rhat).sum(1)[:, None] * rhat                    # remove the radial (global inward) component
    tree = cKDTree(xy)
    c = np.full(len(t), np.nan)
    for i, nb in enumerate(tree.query_ball_point(xy, radius)):
        nb = [j for j in nb if j != i]
        if len(nb) >= 4:
            d = xy[i] - xy[nb]
            d /= np.linalg.norm(d, axis=1)[:, None]
            c[i] = np.mean((vt[nb] * d).sum(1))
    return c


def auxin_sites(t, aux_s):
    """Local maxima of smoothed auxin input in 20-50 um, above the 70th percentile (as handedness.py)."""
    xy = t[["x", "y"]].values
    tree = cKDTree(xy)
    keep = []
    q70 = np.quantile(aux_s, 0.7)
    for i, nb in enumerate(tree.query_ball_point(xy, 8.0)):
        if 20 <= t.r.values[i] <= 50 and aux_s[i] >= aux_s[nb].max() and aux_s[i] >= q70:
            keep.append(i)
    return xy[keep]


def ring_profile(xy, v, sites):
    tree = cKDTree(xy)
    prof = []
    for lo, hi in zip(RINGS[:-1], RINGS[1:]):
        vals = []
        for s in sites:
            idx = [j for j in tree.query_ball_point(s, hi) if np.hypot(*(xy[j] - s)) >= lo]
            vals += list(v[idx])
        vals = np.asarray(vals, float)
        prof.append(np.nanmean(vals) if np.isfinite(vals).any() else np.nan)
    return np.array(prof)


def site_test(t, v, sites, rng):
    """Centre ring minus outer ring around auxin sites, against the same contrast at the sites rotated to random angles."""
    xy = t[["x", "y"]].values
    obs = ring_profile(xy, v, sites)
    rs, th = np.hypot(sites[:, 0], sites[:, 1]), np.arctan2(sites[:, 1], sites[:, 0])
    null = []
    for _ in range(N_NULL):
        a = th + rng.uniform(0, 2 * np.pi, len(th))
        null.append(ring_profile(xy, v, np.c_[rs * np.cos(a), rs * np.sin(a)]))
    null = np.array(null)
    c_obs = obs[0] - np.nanmean(obs[-2:])
    c_null = null[:, 0] - np.nanmean(null[:, -2:], axis=1)
    return obs, null, float(c_obs), float((c_null >= c_obs).mean())


def cellmap(ax, t, values, cmap, lim):
    xy = t[["x", "y"]].values
    ghost = (RMAX + 25) * np.c_[np.cos(np.linspace(0, 2 * np.pi, 80)), np.sin(np.linspace(0, 2 * np.pi, 80))]
    vor = Voronoi(np.vstack([xy, ghost]))
    polys, vals = [], []
    for k in range(len(xy)):
        reg = vor.regions[vor.point_region[k]]
        if reg and -1 not in reg:
            polys.append(vor.vertices[reg]); vals.append(values[k])
    pc = PolyCollection(polys, array=np.array(vals), cmap=cmap, edgecolors=(0, 0, 0, 0.15), linewidths=0.12)
    pc.set_clim(-lim, lim); ax.add_collection(pc); pc.set_clip_path(plt.Circle((0, 0), RMAX, transform=ax.transData))
    ax.set_xlim(-RMAX, RMAX); ax.set_ylim(-RMAX, RMAX); ax.set_aspect("equal"); ax.axis("off")
    return pc


def main():
    rng = np.random.default_rng(0)
    files = sorted(PP.DATA.rglob("*_walls.csv"))
    rows = ["aux", "wall", "cellpin", "conv"]
    labels = {"aux": "Auxin input\n(radial trend removed)", "wall": "PIN1 level, walls\n(radial trend removed)",
              "cellpin": "PIN1 level, cell table\n(radial trend removed)", "conv": "Tangential PIN1\nconvergence"}
    fig, axes = plt.subplots(len(rows), len(files), figsize=(W, W * 1.08))
    fig.subplots_adjust(left=0.13, right=0.99, top=0.96, bottom=0.01, wspace=0.03, hspace=0.04)
    report, profiles = [], {}
    for j, f in enumerate(files):
        t = load(f)
        xy = t[["x", "y"]].values
        aux_s = smooth(xy, -np.log(np.maximum(t.qDII.values, 1e-4)), 4.0)
        maps = {"aux": detrend(t.r.values, aux_s),
                "wall": detrend(t.r.values, smooth(xy, t.wall.values, 4.0)),
                "cellpin": detrend(t.r.values, smooth(xy, t.cellpin.values, 4.0)),
                "conv": tangential_convergence(t)}
        sites = auxin_sites(t, aux_s)
        band = (t.r.values >= BAND[0]) & (t.r.values < BAND[1])
        rec = dict(meristem=short(f.parent.name), cells=int(len(t)), sites=int(len(sites)))
        for k in ("wall", "cellpin", "conv"):
            m = band & np.isfinite(maps[k]) & np.isfinite(maps["aux"])
            rec[f"corr_aux_{k}"] = float(np.corrcoef(maps["aux"][m], maps[k][m])[0, 1])
            obs, null, c, p = site_test(t, maps[k], sites, rng)
            rec[f"site_contrast_{k}"], rec[f"site_p_{k}"] = c, p
            profiles[(rec["meristem"], k)] = (obs, np.nanpercentile(null, [5, 50, 95], axis=0))
        report.append(rec)
        for i, k in enumerate(rows):
            v = maps[k]
            lim = np.nanpercentile(np.abs(v[band]), 95)
            cellmap(axes[i, j], t, np.nan_to_num(v), "RdBu_r" if k != "aux" else "PuOr_r", lim)
            axes[i, j].plot(sites[:, 0], sites[:, 1], "o", ms=5, mfc="none", mec="k", mew=0.8)
            th = np.linspace(0, 2 * np.pi, 200)
            axes[i, j].plot(27.3 * np.cos(th), 27.3 * np.sin(th), ":", color="k", lw=0.6)
        axes[0, j].set_title(rec["meristem"], fontsize=8.5, pad=2)
    for i, k in enumerate(rows):
        axes[i, 0].text(-0.06, 0.5, labels[k], transform=axes[i, 0].transAxes, rotation=90, ha="right", va="center", fontsize=7.5)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_X2_pin1_level_detrended.{ext}")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(W, W * 0.4))
    fig.subplots_adjust(left=0.11, right=0.99, top=0.82, bottom=0.2, wspace=0.42)
    short_t = {"wall": "PIN1 level, walls", "cellpin": "PIN1 level, cell table", "conv": "Tangential convergence"}
    mid = 0.5 * (RINGS[:-1] + RINGS[1:])
    cols = dict(zip([r["meristem"] for r in report], ["#1b9e77", "#d95f02", "#7570b3", "#e7298a"]))
    for ax, k in zip(axes, ("wall", "cellpin", "conv")):
        for r in report:
            obs, (lo, md, hi) = profiles[(r["meristem"], k)]
            ax.fill_between(mid, lo, hi, color=cols[r["meristem"]], alpha=0.12, lw=0)
            ax.plot(mid, obs, "-o", ms=2.5, lw=0.9, color=cols[r["meristem"]], label=r["meristem"])
        ax.axhline(0, color="k", lw=0.5)
        ax.set_title(short_t[k], fontsize=8)
    axes[1].set_xlabel("Distance from auxin-input maximum (µm)")
    axes[0].set_ylabel("Residual after radial trend")
    fig.text(0.5, 0.97, "Lines: around auxin-input maxima; bands: same sites rotated to random angles (5–95%)", ha="center", va="top", fontsize=7.5)
    axes[0].legend(frameon=False, fontsize=6, loc="upper right", ncol=2)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_X3_pin1_site_profiles.{ext}")
    plt.close(fig)

    json.dump(report, open(OUT / "explore_pin1_level.json", "w"), indent=1)
    for r in report:
        print(f"{r['meristem']:10s} cells {r['cells']:4d} auxin sites {r['sites']}  | corr with auxin (15-50 um, detrended): "
              f"walls {r['corr_aux_wall']:+.2f}  cell table {r['corr_aux_cellpin']:+.2f}  convergence {r['corr_aux_conv']:+.2f}  | "
              f"site contrast (P vs random angle): walls {r['site_contrast_wall']:+.3f} ({r['site_p_wall']:.2f})  "
              f"cell table {r['site_contrast_cellpin']:+.3f} ({r['site_p_cellpin']:.2f})  convergence {r['site_contrast_conv']:+.4f} ({r['site_p_conv']:.2f})")


if __name__ == "__main__":
    main()
