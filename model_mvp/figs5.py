"""Static side-by-side: measured auxin proxy on a real meristem (E27/SAM7, 0 h, user's reproduction
of Galvan-Ampudia 2020) versus one model snapshot, on the same spatial scale."""
import csv
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi

import figs  # noqa: F401
import viz
from e10_phase_sub import OP
from model import Sim

from pathlib import Path

BASE = str(Path(__file__).resolve().parents[1] / "reproductions" / "elife55832" / "outputs" / "historic_nuclei_images"
           / "qDII-DR5-CLV3-LD_E27_170817_sam07" / "qDII-DR5-CLV3-LD_E27_170817_sam07_t00"
           / "qDII-DR5-CLV3-LD_E27_170817_sam07_t00_")
CELL_UM = 6.0   # one model length unit, from ~574 L1 cells over the imaged disc


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


if __name__ == "__main__":
    cells = read(BASE + "aligned_L1_normalized_signal_data.csv")
    x = np.array([float(c["aligned_x"]) for c in cells]); y = np.array([float(c["aligned_y"]) for c in cells])
    aux = np.array([float(c["Auxin"]) for c in cells]); rclv = float(cells[0]["clv3_radius"])
    ext = [e for e in read(BASE + "aligned_primordia_extrema.csv") if e["extremum_type"] == "minimum"]
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
    ax = axs[0]
    P = np.c_[x, y]; R = np.hypot(x, y).max()
    ang = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    vor = Voronoi(np.vstack([P, (R + 8) * np.c_[np.cos(ang), np.sin(ang)]]))
    polys = [vor.vertices[vor.regions[vor.point_region[k]]] for k in range(len(P))]
    pc = PolyCollection(polys, array=aux, cmap="viridis", edgecolors="k", linewidths=0.15); ax.add_collection(pc)
    plt.colorbar(pc, ax=ax, fraction=0.046, pad=0.02, label="生长素代理 1 − qDII")
    ax.add_patch(plt.Circle((0, 0), rclv, fill=False, color="r", ls="--", lw=1.0))
    for e in ext:
        ax.text(float(e["aligned_x"]), float(e["aligned_y"]), "P" + e["primordium"], color="w", fontsize=8, ha="center", va="center", weight="bold")
    ax.set_title(f"实测：E27/SAM7，0 h，L1 层 {len(P)} 个细胞\n红圈为 CLV3 半径 {rclv:.0f} µm；标注为生长素最大区的阶段", fontsize=10)
    sim = Sim(dict(OP, R_c=4.5, R_p=6.5, R_out=13.5, w=3.5, t_end=600.0, snap_dt=599.0)).run()
    sn = sim.snaps[-1]
    ax = axs[1]
    pm = dict(sim.p);
    polys = [CELL_UM * q for q in viz.polygons(sn["pts"], sim.p["R_out"])]
    pc = PolyCollection(polys, array=sn["A"], cmap="viridis", edgecolors="k", linewidths=0.15); ax.add_collection(pc)
    plt.colorbar(pc, ax=ax, fraction=0.046, pad=0.02, label="模型生长素浓度")
    for rr in (sim.p["R_c"], sim.p["R_p"]):
        ax.add_patch(plt.Circle((0, 0), CELL_UM * rr, fill=False, color="r", ls="--", lw=1.0))
    for (px, py, pid, age) in sn["prim"]:
        ax.text(CELL_UM * px, CELL_UM * py, "●", color="w", fontsize=8, ha="center", va="center")
    ax.set_title(f"模型：螺旋工作点的一帧（1 个长度单位按 {CELL_UM:g} µm 换算）\n红圈为发生环内外边界；白点为原基中心", fontsize=10)
    for a in axs:
        a.set_xlim(-82, 82); a.set_ylim(-82, 82); a.set_aspect("equal"); a.set_xlabel("µm")
    fig.suptitle("同一比例下的静态对照：实测中央区为高生长素，模型基线中央区偏低", fontsize=12)
    fig.tight_layout(); fig.savefig("out/fig_data_vs_model.png", dpi=110); plt.close(fig); print("saved out/fig_data_vs_model.png")
    r = np.hypot(x, y)
    print("measured mean auxin proxy: r<clv3 %.2f | clv3..1.5clv3 %.2f | beyond %.2f" % (aux[r < rclv].mean(), aux[(r >= rclv) & (r < 1.5 * rclv)].mean(), aux[r >= 1.5 * rclv].mean()))
