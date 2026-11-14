"""Two explanatory figures for the progress note: the grouping of the meristems and the side-naming issue.

python fig_progress.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 400})
W = 13.5 / 2.54
C_FIT, C_HELD, C_PIN, C_DEV = "#2166ac", "#d6604d", "#1b7837", "#7f7f7f"


def fig_groups():
    batches = [("DR5-TEST", "2017-02-26", 3, C_FIT), ("E25", "2017-08-11", 6, C_FIT), ("E27", "2017-08-17", 5, C_FIT),
               ("E31", "2017-11-02", 2, C_HELD), ("E33", "2017-11-06", 5, C_HELD), ("E35", "2017-11-10", 2, C_PIN), ("E37", "2017-11-13", 2, C_PIN)]
    fig, ax = plt.subplots(figsize=(W, W * 0.36))
    fig.subplots_adjust(left=0.03, right=0.99, top=0.86, bottom=0.26)
    for k, (name, date, n, col) in enumerate(batches):
        for j in range(n):
            ax.plot(k, j, "o", ms=8, color=col, mec="k" if col != C_HELD else col, mew=0.4, mfc=col if col != C_HELD else "none")
        ax.text(k, -1.0, f"{name}\n{date}", ha="center", va="top", fontsize=7.5)
    ax.plot(2, 5, "*", ms=10, color=C_DEV, mec="k", mew=0.4)
    ax.text(2.18, 5, "E27 SAM7 (development only)", va="center", fontsize=7)
    for x0, x1, lab, col in ((-0.35, 2.35, "Parameter group: 14 meristems", C_FIT), (2.65, 4.35, "Held out: 7 (not read)", C_HELD),
                             (4.65, 6.35, "PIN1: 4 (0 h only)", C_PIN)):
        ax.plot([x0, x1], [6.6, 6.6], color=col, lw=2, solid_capstyle="butt")
        ax.text(0.5 * (x0 + x1), 6.9, lab, ha="center", va="bottom", color=col, fontsize=8)
    ax.set_xlim(-0.6, 6.6); ax.set_ylim(-0.6, 7.6); ax.axis("off")
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_P1_groups.{ext}")
    plt.close(fig)


def wall(ax, title, left_name, right_name):
    ax.add_patch(Rectangle((0, 0), 1.9, 2, fc="#f2f2f2", ec="k", lw=0.6)); ax.add_patch(Rectangle((2.1, 0), 1.9, 2, fc="#f2f2f2", ec="k", lw=0.6))
    ax.add_patch(Rectangle((1.9, 0), 0.2, 2, fc="#bdbdbd", ec="none"))
    ax.add_patch(Rectangle((1.55, 0), 0.35, 2, fc="#1b7837", ec="none", alpha=0.55)); ax.add_patch(Rectangle((2.1, 0), 0.35, 2, fc="#762a83", ec="none", alpha=0.55))
    ax.text(0.75, 1.0, "left cell", ha="center", va="center"); ax.text(3.25, 1.0, "right cell", ha="center", va="center")
    ax.add_patch(FancyArrowPatch((1.3, 2.25), (2.7, 2.25), arrowstyle="-|>", mutation_scale=8, lw=0.8, color="k"))
    ax.text(2.0, 2.33, "wall normal", ha="center", va="bottom", fontsize=7)
    ax.annotate(left_name, (1.72, 0.0), (0.75, -0.5), ha="center", va="top", fontsize=7.5, color="#1b7837", arrowprops=dict(arrowstyle="-", lw=0.5, color="#1b7837"))
    ax.annotate(right_name, (2.28, 0.0), (3.25, -0.5), ha="center", va="top", fontsize=7.5, color="#762a83", arrowprops=dict(arrowstyle="-", lw=0.5, color="#762a83"))
    ax.set_title(title, fontsize=8.5, pad=10)
    ax.set_xlim(-0.1, 4.1); ax.set_ylim(-1.5, 2.7); ax.set_aspect("equal"); ax.axis("off")


def fig_sides():
    checks = json.load(open(OUT / "pin1_convention_checks.json"))
    fig, axes = plt.subplots(1, 3, figsize=(W, W * 0.4), gridspec_kw=dict(width_ratios=[1, 1, 0.72]))
    fig.subplots_adjust(left=0.035, right=0.985, top=0.8, bottom=0.22, wspace=0.42)
    wall(axes[0], "Library builds 10–21 (our data)", "column\nright_PIN1", "column\nleft_PIN1")
    wall(axes[1], "Library build 23", "column\nleft_PIN1", "column\nright_PIN1")
    ax = axes[2]
    names = [c["frame"].split("_")[1] + " SAM" + str(int(c["frame"].split("_")[3][3:])) for c in checks]
    ax.bar(range(len(checks)), [c["polarity_agrees_with_right_minus_left"] for c in checks], color="#636363", width=0.6)
    ax.axhline(0.9, color="k", lw=0.6, ls="--"); ax.axhline(0.1, color="k", lw=0.6, ls=":")
    ax.set_xticks(range(len(checks)), names, rotation=30, ha="right", fontsize=7); ax.set_ylim(0, 1.08)
    ax.set_ylabel("Fraction of walls", fontsize=7.5); ax.set_title("Polarity sign =\nsign(right − left by name)", fontsize=8)
    for a, s in zip(axes, "ABC"):
        box = a.get_subplotspec().get_position(fig)
        fig.text(box.x0 - (0.03 if s != "C" else 0.085), 0.86, s, fontsize=11, fontweight="bold", family="DejaVu Sans")
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_P2_side_naming.{ext}")
    plt.close(fig)


if __name__ == "__main__":
    fig_groups()
    fig_sides()
