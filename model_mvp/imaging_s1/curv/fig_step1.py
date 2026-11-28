"""Figure S1-2: feasibility of blind morphology labelling (implementation plan step 1). Development group only; no signals.

python fig_step1.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from curvlib import FRAMES, apex, load_seq
from export_codex import dome_residual

HERE = Path(__file__).resolve().parent
G = json.load(open(HERE.parent / "groups.json"))
KEY = json.load(open(HERE / "out" / "blind_key.json"))["key"]
DATA = HERE.parents[2] / "reproductions" / "elife55832" / "outputs" / "nuclei_21"
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 400})
W = 13.5 / 2.54
EXAMPLE = "M04"
FRAME_OF = {"visible_0h": 0, "event_0_5": 1, "event_5_10": 2}
COL = {"visible_0h": "#4d4d4d", "event_0_5": "#1b9e77", "event_5_10": "#d95f02"}


def main():
    auto = pd.read_csv(HERE / "out" / "auto_sites_development.csv")
    auto["kind"] = [("visible_0h" if l == "visible_at_0h" else ("event_0_5" if i == "(0,5]" else "event_5_10") if l == "event" else "unclear")
                   for l, i in zip(auto.label, auto.interval.fillna(""))]
    cx = pd.read_csv(HERE / "codex_returned" / "labels.csv", dtype={"first_visible": str})
    cx = cx[cx.first_visible != "none"]
    cx["kind"] = cx.first_visible.map({"0": "visible_0h", "5": "event_0_5", "10": "event_5_10"}).fillna("unclear")
    S = pd.read_csv(HERE / "out" / "agreement_sites.csv")
    R = S[S.in_region]

    fig = plt.figure(figsize=(W, W * 0.78))
    gs = fig.add_gridspec(2, 6, height_ratios=[1.15, 1.0], hspace=0.45, wspace=0.9, left=0.07, right=0.98, top=0.93, bottom=0.16)
    gb = gs[1, :].subgridspec(1, 3, width_ratios=[1, 1, 1.25], wspace=0.75)
    name = KEY[EXAMPLE]
    seq = load_seq(DATA / name); c = apex(seq["t00"])
    a_m, c_m = auto[auto.meristem == name], cx[cx.code == EXAMPLE]
    th = np.linspace(0, 2 * np.pi, 200)
    for j, fr in enumerate(FRAMES):
        ax = fig.add_subplot(gs[0, 2 * j:2 * j + 2])
        d = seq[fr]; x, y = d.x.values - c[0], d.y.values - c[1]
        sc = ax.scatter(x, y, c=dome_residual(x, y, d.z.values), cmap="PuOr_r", vmin=-4, vmax=4, s=3, lw=0)
        for r in (22, 48):
            ax.plot(r * np.cos(th), r * np.sin(th), ":", color="k", lw=0.6)
        for _, s in a_m.iterrows():
            if FRAME_OF.get(s["kind"]) == j:
                ax.plot(s.x, s.y, "o", ms=8, mfc="none", mec=COL[s["kind"]], mew=1.3)
        for _, s in c_m.iterrows():
            if FRAME_OF.get(s["kind"]) == j:
                ax.plot(s.x_um, s.y_um, "^", ms=6, mfc="none", mec=COL[s["kind"]], mew=1.1)
        ax.set_xlim(-60, 60); ax.set_ylim(-60, 60); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(f"{int(fr[1:])} h", fontsize=9, pad=2)
        if j == 0:
            ax.plot([-55, -35], [-58, -58], color="k", lw=1.5); ax.text(-45, -56, "20 µm", ha="center", va="bottom", fontsize=7)
    hs = [plt.Line2D([], [], ls="", marker="o", mfc="none", mec="k", ms=6, label="Auto"),
          plt.Line2D([], [], ls="", marker="^", mfc="none", mec="k", ms=5, label="Codex"),
          plt.Line2D([], [], ls="", marker="s", color=COL["visible_0h"], ms=5, label="visible at 0 h"),
          plt.Line2D([], [], ls="", marker="s", color=COL["event_0_5"], ms=5, label="first at 5 h"),
          plt.Line2D([], [], ls="", marker="s", color=COL["event_5_10"], ms=5, label="first at 10 h")]
    fig.legend(handles=hs, loc="upper center", ncol=5, frameon=False, fontsize=7, columnspacing=1.2, handletextpad=0.3, bbox_to_anchor=(0.5, 1.0))

    J = lambda s: s.isin(["event_0_5", "event_5_10"])
    ja, jc = J(R.auto), J(R.codex)
    groups = {"Auto": ja, "Codex": jc, "Both": ja & jc}
    ax = fig.add_subplot(gb[0])
    tot = [int(m.sum()) for m in groups.values()]
    ax.bar(range(3), tot, color=["#7f7f7f", "#3182bd", "#1b7837"], width=0.6)
    ax.axhline(20, color="k", lw=0.7, ls="--"); ax.text(2.45, 20.5, "required ≥ 20", ha="right", va="bottom", fontsize=7)
    ax.set_xticks(range(3), list(groups)); ax.set_ylabel("Judgeable events"); ax.set_ylim(0, 24)
    for k, v in enumerate(tot):
        ax.text(k, v + 0.4, str(v), ha="center", fontsize=7)
    ax = fig.add_subplot(gb[1])
    mer = [int((R[m].groupby("meristem").size() > 0).sum()) for m in groups.values()]
    ax.bar(range(3), mer, color=["#7f7f7f", "#3182bd", "#1b7837"], width=0.6)
    ax.axhline(8, color="k", lw=0.7, ls="--"); ax.text(2.45, 8.3, "required ≥ 8", ha="right", va="bottom", fontsize=7)
    ax.set_xticks(range(3), list(groups)); ax.set_ylabel("Meristems with an event"); ax.set_ylim(0, 14)
    for k, v in enumerate(mer):
        ax.text(k, v + 0.25, str(v), ha="center", fontsize=7)
    ax = fig.add_subplot(gb[2])
    order = ["visible_0h", "event_0_5", "event_5_10", "unclear", "absent"]
    lab = ["0 h", "5 h", "10 h", "unclear", "not marked"]
    M = pd.crosstab(R.auto, R.codex).reindex(index=order, columns=order, fill_value=0).values
    ax.imshow(M, cmap="Greys", vmin=0, vmax=M.max() * 1.6)
    for i in range(5):
        for k in range(5):
            if M[i, k]:
                ax.text(k, i, str(M[i, k]), ha="center", va="center", fontsize=7, color="k")
    ax.set_xticks(range(5), lab, rotation=40, ha="right", fontsize=6.5); ax.set_yticks(range(5), lab, fontsize=6.5)
    ax.set_xlabel("Codex: first visible", fontsize=7.5); ax.set_ylabel("Automatic: first visible", fontsize=7.5, labelpad=1)
    ax.spines[:].set_visible(True)
    ax.set_title("κ = 0.09 (required ≥ 0.6)", fontsize=8)
    for ext in ("png", "pdf"):
        fig.savefig(HERE / "out" / f"fig_S1-2_blind_morphology.{ext}")


if __name__ == "__main__":
    main()
