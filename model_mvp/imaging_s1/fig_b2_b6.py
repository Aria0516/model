"""Figures for plan step 3: B2 (central/peripheral PIN1 signal ratio) and B6 (growth estimator validation)."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 400})
W = 13.5 / 2.54


def b2():
    recs = json.load(open(OUT / "b2_regional.json"))
    val = json.load(open(OUT / "b2_validation.json"))
    name = lambda f: f.split("_")[1] + " SAM" + str(int(f.split("_")[3][3:]))
    fig, ax = plt.subplots(figsize=(W * 0.55, W * 0.55))
    fig.subplots_adjust(left=0.17, right=0.97, top=0.9, bottom=0.36)
    keys = [("wall_ratio_own", "Walls, own CZ radius", "o", "#1b7837"), ("wall_ratio_fixed", "Walls, 27.3 µm", "s", "#5aae61"),
            ("cell_ratio_own", "Cell table, own radius", "^", "#7f7f7f"), ("cell_ratio_fixed", "Cell table, 27.3 µm", "v", "#bdbdbd")]
    for j, (k, lab, mk, col) in enumerate(keys):
        for i, r in enumerate(recs):
            ax.plot(i + (j - 1.5) * 0.12, r[k], mk, ms=4, color=col, mfc=col if "wall" in k else "none", label=lab if i == 0 else None)
    ax.axhline(1, color="k", lw=0.5, ls=":")
    ax.axhline(val["code_ratio"], color="#b2182b", lw=0.9, ls="--")
    ax.text(3.45, val["code_ratio"] + 0.04, "model main line (same measure)", color="#b2182b", ha="right", fontsize=6.5)
    ax.set_xticks(range(len(recs)), [name(r["frame"]) + ("\n(incomplete)" if "sam06" in r["frame"] else "") for r in recs],
                  rotation=0, fontsize=7)
    ax.set_ylabel("PIN1 signal, centre / periphery"); ax.set_ylim(0, 1.7)
    ax.legend(frameon=False, fontsize=6, loc="upper center", ncol=2, bbox_to_anchor=(0.45, -0.22))
    ax.set_title("Central-zone PIN1 signal relative to periphery", fontsize=8.5)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_S1-4_pin1_centre_periphery.{ext}")
    plt.close(fig)


def b6():
    d = pd.DataFrame(json.load(open(OUT / "b6_validation.json")))
    bands = ["10-25", "25-40", "40-52"]
    fig, axes = plt.subplots(1, 3, figsize=(W, W * 0.38), sharey=True)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.82, bottom=0.2, wspace=0.12)
    lim = (-0.015, 0.05)
    for ax, b in zip(axes, bands):
        x = d[d.band == b]
        for t, g in x.groupby("true"):
            jit = np.linspace(-0.0012, 0.0012, len(g))
            ax.plot(t + jit, g.est, "o", ms=2, color="#3182bd", alpha=0.6)
        tt = np.array(sorted(d.true.unique()))
        ax.fill_between([lim[0], lim[1]], [lim[0] * 0.85, lim[1] * 0.85], [lim[0] * 1.15, lim[1] * 1.15], color="#e0e0e0", lw=0)
        ax.plot(lim, lim, "k-", lw=0.6)
        ax.set_xlim(-0.004, 0.034); ax.set_ylim(*lim)
        ax.set_title(f"Arc length {b} µm", fontsize=8)
        ax.set_xlabel("True growth rate (1/h)")
    axes[0].set_ylabel("Estimated (1/h)")
    fig.text(0.5, 0.97, "Growth-rate estimator on synthetic domes (5 h frame pairs): grey band = ±15% (pre-specified)",
             ha="center", va="top", fontsize=7.5)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_S1-5_growth_estimator_validation.{ext}")
    plt.close(fig)


if __name__ == "__main__":
    b2(); b6()
