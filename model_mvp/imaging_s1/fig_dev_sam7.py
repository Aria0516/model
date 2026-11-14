"""Figure S1-0: the development meristem E27/SAM7 (outside the 21) at 0, 5 and 10 h: auxin input, DR5 output and
the automatically labelled input maxima. Illustration only; no statistic is taken from it.

python fig_dev_sam7.py
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi

HERE = Path(__file__).resolve().parent
SEQ = "qDII-DR5-CLV3-LD_E27_170817_sam07"
ROOT = HERE.parents[1] / "reproductions" / "elife55832" / "outputs" / "validate_auto_crop" / SEQ
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "savefig.dpi": 400})
W, RMAX = 13.5 / 2.54, 58.0


def frame(h):
    stem = ROOT / f"{SEQ}_t{h:02d}" / f"{SEQ}_t{h:02d}_"
    return pd.read_csv(str(stem) + "aligned_L1_normalized_signal_data.csv"), pd.read_csv(str(stem) + "aligned_primordia_extrema.csv")


def cells(ax, d, values, cmap, vmin, vmax):
    xy = d[["aligned_x", "aligned_y"]].values
    keep = np.hypot(xy[:, 0], xy[:, 1]) < RMAX + 12
    xy, values = xy[keep], np.asarray(values)[keep]
    ghost = (RMAX + 30) * np.c_[np.cos(np.linspace(0, 2 * np.pi, 80)), np.sin(np.linspace(0, 2 * np.pi, 80))]
    vor = Voronoi(np.vstack([xy, ghost]))
    polys, vals = [], []
    for k in range(len(xy)):
        reg = vor.regions[vor.point_region[k]]
        if reg and -1 not in reg:
            polys.append(vor.vertices[reg]); vals.append(values[k])
    pc = PolyCollection(polys, array=np.array(vals), cmap=cmap, edgecolors=(0, 0, 0, 0.25), linewidths=0.15)
    pc.set_clim(vmin, vmax)
    ax.add_collection(pc)
    clip = plt.Circle((0, 0), RMAX, transform=ax.transData)
    pc.set_clip_path(clip)
    ax.set_xlim(-RMAX, RMAX); ax.set_ylim(-RMAX, RMAX); ax.set_aspect("equal"); ax.axis("off")
    return pc


def main():
    data = {h: frame(h) for h in (0, 5, 10)}
    dr5 = np.concatenate([d["DR5"].values for d, _ in data.values()])
    lo, hi = np.percentile(dr5, [2, 99])
    fig, axes = plt.subplots(2, 3, figsize=(W, W * 0.72))
    fig.subplots_adjust(left=0.05, right=0.9, top=0.94, bottom=0.03, wspace=0.04, hspace=0.06)
    th = np.linspace(0, 2 * np.pi, 200)
    for j, h in enumerate((0, 5, 10)):
        d, e = data[h]
        pa = cells(axes[0, j], d, d["Auxin"].values, "viridis", 0.55, 1.0)
        pd5 = cells(axes[1, j], d, d["DR5"].values, "magma", lo, hi)
        rc = d["clv3_radius"].iloc[0]
        m = e[(e.extremum_type == "minimum") & (e.radial_distance < RMAX - 3)]
        for ax in axes[:, j]:
            ax.plot(rc * np.cos(th), rc * np.sin(th), "--", color="w", lw=0.8)
            for _, q in m.iterrows():
                ax.plot(q.aligned_x, q.aligned_y, "o", ms=6, mfc="none", mec="w", mew=0.9)
                ax.text(q.aligned_x, q.aligned_y + 5, f"P{int(q.primordium)}", color="w", ha="center", va="bottom", fontsize=7, fontweight="bold",
                        path_effects=[matplotlib.patheffects.withStroke(linewidth=1.2, foreground="k")])
        axes[0, j].set_title(f"{h} h", fontsize=9, pad=2)
    axes[1, 0].plot([-58, -38], [-60, -60], color="k", lw=1.5, clip_on=False)
    axes[1, 0].text(-48, -62, "20 µm", color="k", ha="center", va="top", fontsize=7)
    for ax, pc, lab in ((axes[0, 2], pa, "Auxin input (1 − $qDII$)"), (axes[1, 2], pd5, "$DR5$ output")):
        cax = ax.inset_axes([1.04, 0.15, 0.045, 0.7])
        cb = fig.colorbar(pc, cax=cax, ticks=[]); cb.outline.set_linewidth(0.4)
        cax.set_ylabel(lab, fontsize=8); cax.text(0.5, -0.03, "low", transform=cax.transAxes, ha="center", va="top", fontsize=7)
        cax.text(0.5, 1.03, "high", transform=cax.transAxes, ha="center", va="bottom", fontsize=7)
    for ext in ("png", "pdf"):
        fig.savefig(HERE / "out" / f"fig_S1-0_dev_meristem_timeseries.{ext}")


if __name__ == "__main__":
    import matplotlib.patheffects  # noqa: F401
    main()
