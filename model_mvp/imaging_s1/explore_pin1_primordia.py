"""Exploratory (not pre-specified): do the PIN1 tables show primordia? For each of the 4 PIN1 meristems, top row:
auxin input (low qDII) per L1 cell with the net efflux arrows; bottom row: PIN1 level per cell (wall PIN1 / PI).

python explore_pin1_primordia.py
"""
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
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "savefig.dpi": 400})
W, RMAX = 13.5 / 2.54, 52.0


def tables(f):
    w, cells = PP.load(f)
    l1 = cells[cells.layer == 1]
    cen = PP.centre(l1)
    s = PP.sides(w, set(l1.label), True)
    other = s.rename(columns={"cell": "other", "other": "cell", "PIN1": "PIN1_n", "PI": "PI_n"})[["cell", "other", "PIN1_n", "PI_n"]]
    s = s.merge(other, on=["cell", "other"])
    xy = cells.set_index("label")[["center_x", "center_y"]]
    e = xy.loc[s.other].values - xy.loc[s.cell].values
    e /= np.hypot(e[:, 0], e[:, 1])[:, None]
    asym = ((s.PIN1 - s.PIN1_n) / (s.PIN1 + s.PIN1_n)).values
    g = pd.DataFrame(dict(cell=s.cell.values, ax=s.area.values * asym * e[:, 0], ay=s.area.values * asym * e[:, 1], a=s.area.values,
                          lev=s.area.values * (s.PIN1 / s.PI).values)).groupby("cell").sum()
    t = pd.DataFrame(dict(vx=g.ax / g.a, vy=g.ay / g.a, pin=g.lev / g.a))
    pos = xy.loc[t.index].values - cen
    t["x"], t["y"] = pos[:, 0], pos[:, 1]
    t["qDII"] = cells.set_index("label").loc[t.index, "qDII"].values
    return t[np.hypot(t.x, t.y) < RMAX + 6]


def smooth(t, col, radius=6.0):
    tree = cKDTree(t[["x", "y"]].values)
    v = t[col].values
    return np.array([np.nanmedian(v[nb]) for nb in tree.query_ball_point(t[["x", "y"]].values, radius)])


def cellmap(ax, t, values, cmap, lo, hi):
    xy = t[["x", "y"]].values
    ghost = (RMAX + 25) * np.c_[np.cos(np.linspace(0, 2 * np.pi, 80)), np.sin(np.linspace(0, 2 * np.pi, 80))]
    vor = Voronoi(np.vstack([xy, ghost]))
    polys, vals = [], []
    for k in range(len(xy)):
        reg = vor.regions[vor.point_region[k]]
        if reg and -1 not in reg:
            polys.append(vor.vertices[reg]); vals.append(values[k])
    pc = PolyCollection(polys, array=np.array(vals), cmap=cmap, edgecolors=(0, 0, 0, 0.2), linewidths=0.15)
    pc.set_clim(lo, hi); ax.add_collection(pc); pc.set_clip_path(plt.Circle((0, 0), RMAX, transform=ax.transData))
    ax.set_xlim(-RMAX, RMAX); ax.set_ylim(-RMAX, RMAX); ax.set_aspect("equal"); ax.axis("off")
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(27.3 * np.cos(th), 27.3 * np.sin(th), "--", color="w", lw=0.7)
    return pc


def main():
    files = sorted(PP.DATA.rglob("*_walls.csv"))
    fig, axes = plt.subplots(2, 4, figsize=(W, W * 0.56))
    fig.subplots_adjust(left=0.035, right=0.91, top=0.93, bottom=0.02, wspace=0.03, hspace=0.05)
    for j, f in enumerate(files):
        t = tables(f)
        aux = -np.log(np.maximum(smooth(t, "qDII", 4.0), 1e-4))
        pa = cellmap(axes[0, j], t, aux, "viridis", *np.percentile(aux, [5, 97]))
        n = np.hypot(t.vx, t.vy).values
        L = 4.2 * np.minimum(n / np.percentile(n, 90), 1.0) / np.maximum(n, 1e-12)
        m = (np.hypot(t.x, t.y) < RMAX - 2).values
        axes[0, j].quiver(t.x[m], t.y[m], (t.vx * L)[m], (t.vy * L)[m], color="w", angles="xy", scale_units="xy", scale=1, width=0.006,
                          headwidth=3.2, headlength=3.4, headaxislength=3.0, minlength=0.5, pivot="mid")
        lp = np.log(t.pin.values)
        pp = cellmap(axes[1, j], t, lp, "magma", *np.percentile(lp, [5, 98]))
        p = f.parent.name.split("_")
        axes[0, j].set_title(f"{p[1]} SAM{int(p[3][3:])}", fontsize=8.5, pad=2)
        print(f.parent.name[-28:], "cells", len(t), "corr(-ln qDII smoothed, ln PIN1/PI) =",
              round(float(np.corrcoef(aux[m], lp[m])[0, 1]), 3))
    for ax, pc, lab in ((axes[0, 3], pa, "Auxin input (low $qDII$)"), (axes[1, 3], pp, "PIN1 level (wall PIN1 / PI)")):
        cax = ax.inset_axes([1.05, 0.12, 0.05, 0.76])
        cb = fig.colorbar(pc, cax=cax, ticks=[]); cb.outline.set_linewidth(0.4); cax.set_ylabel(lab, fontsize=7.5)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_X1_pin1_primordia_exploratory.{ext}")


if __name__ == "__main__":
    main()


def tangential_check():
    """Exploratory: outside the global inward trend, does the efflux direction follow the local gradient of auxin input?
    Both vectors are projected on the tangential direction; report how often the two components have the same sign."""
    for f in sorted(PP.DATA.rglob("*_walls.csv")):
        t = tables(f)
        xy = t[["x", "y"]].values
        aux = -np.log(np.maximum(smooth(t, "qDII", 4.0), 1e-4))
        tree = cKDTree(xy)
        grad = np.full((len(t), 2), np.nan)
        for i, nb in enumerate(tree.query_ball_point(xy, 10.0)):
            if len(nb) >= 6:
                A = np.c_[xy[nb] - xy[i], np.ones(len(nb))]
                grad[i] = np.linalg.lstsq(A, aux[nb], rcond=None)[0][:2]
        r = np.hypot(xy[:, 0], xy[:, 1])
        that = np.c_[-xy[:, 1], xy[:, 0]] / np.maximum(r, 1e-9)[:, None]
        gt = (grad * that).sum(1)
        vt = (t[["vx", "vy"]].values * that).sum(1)
        m = (r >= 25) & (r < 50) & np.isfinite(gt) & np.isfinite(vt)
        strong = m & (np.abs(gt) >= np.nanmedian(np.abs(gt[m])))
        rng = np.random.default_rng(0)
        same = np.sign(gt[strong]) == np.sign(vt[strong])
        bs = same[rng.integers(0, len(same), (1000, len(same)))].mean(1)
        print(f"{f.parent.name[-28:]}  cells 25-50 um with a clear tangential auxin gradient: {int(strong.sum())}  "
              f"efflux follows the gradient tangentially in {same.mean():.3f} [{np.percentile(bs, 2.5):.3f},{np.percentile(bs, 97.5):.3f}]  (0.5 = unrelated)")
