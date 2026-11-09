"""Plots: tissue snapshot with PIN arrows, ring kymograph, divergence sequence."""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi

from tissue import _ghost_ring


def polygons(pts, R_out):
    P = np.vstack([pts, _ghost_ring(R_out + 0.8)])
    vor = Voronoi(P)
    return [vor.vertices[vor.regions[vor.point_region[k]]] for k in range(len(pts))]


def draw_tissue(ax, pts, val, prim, p, vmin=None, vmax=None, cmap="viridis", pin=None, label=True, cbar=None):
    pc = PolyCollection(polygons(pts, p["R_out"]), array=val, cmap=cmap, edgecolors="k", linewidths=0.15)
    pc.set_clim(vmin, vmax)
    ax.add_collection(pc)
    if pin is not None:
        ax.quiver(pts[:, 0], pts[:, 1], pin[:, 0], pin[:, 1], color="w", scale=28, width=0.0035, headwidth=4)
    for (x, y, pid, age) in prim:
        ax.add_patch(plt.Circle((x, y), p["w"], fill=False, color="w", lw=0.8))
        if label:
            ax.text(x, y, str(pid), color="w", ha="center", va="center", fontsize=7, weight="bold")
    for R in (p["R_c"], p["R_p"]):
        ax.add_patch(plt.Circle((0, 0), R, fill=False, color="r", ls="--", lw=0.7))
    L = p["R_out"]
    ax.set_xlim(-L, L); ax.set_ylim(-L, L); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    if cbar:
        plt.colorbar(pc, ax=ax, fraction=0.046, pad=0.02, label=cbar)
    return pc


def diagnostic(sim, path, title=""):
    p = sim.p
    fig = plt.figure(figsize=(17, 9))
    gs = fig.add_gridspec(2, 4)
    snaps = sim.snaps[-3:]
    vmax = max(s["A"].max() for s in snaps)
    for k, s in enumerate(snaps):
        ax = fig.add_subplot(gs[0, k])
        draw_tissue(ax, s["pts"], s["A"], s["prim"], p, 0, vmax, cbar="auxin" if k == 2 else None)
        ax.set_title(f"t = {s['t']:.0f}")
    ax = fig.add_subplot(gs[0, 3])
    t = np.array([l[0] for l in sim.log]); th = np.degrees(np.arctan2([l[2] for l in sim.log], [l[1] for l in sim.log])) % 360
    d = np.diff(th) % 360
    ax.plot(np.arange(1, len(th)), d, "o-", ms=3, lw=0.8)
    for a in (137.5, 222.5):
        ax.axhline(a, color="r", ls="--", lw=0.8)
    ax.axhline(180, color="gray", ls=":", lw=0.8)
    ax.set_ylim(0, 360); ax.set_xlabel("primordium index"); ax.set_ylabel("signed divergence (deg)")
    if sim.kymo:
        ax = fig.add_subplot(gs[1, :3])
        kt = np.array([k[0] for k in sim.kymo]); km = np.array([k[1] for k in sim.kymo])
        im = ax.imshow(km.T, aspect="auto", origin="lower", extent=[kt[0], kt[-1], 0, 360], cmap="viridis")
        ax.plot(t, th, "wo", ms=3.5, mec="k", mew=0.5)
        ax.set_xlabel("time"); ax.set_ylabel("azimuth in competent ring (deg)")
        plt.colorbar(im, ax=ax, fraction=0.02, pad=0.01, label="ring auxin")
    ax = fig.add_subplot(gs[1, 3])
    ax.plot(t[1:], np.diff(t), "o-", ms=3, lw=0.8); ax.set_xlabel("time"); ax.set_ylabel("interval between initiations")
    fig.suptitle(title); fig.tight_layout(); fig.savefig(path, dpi=95); plt.close(fig)
