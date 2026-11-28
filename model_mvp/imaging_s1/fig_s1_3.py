"""Figure S1-3 (revision 5): staged auxin input and DR5, published target vs development group (exploratory), DR5 delay.

Reads out/staged_signals/ (python s1_staged.py signals) and ga2020/fig4GH_digitized.csv.
Curves are indexed to a common base (0 = baseline, 1 = plateau of each curve), so the two measures share one axis and
t50 is where a curve crosses 0.5.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
SIG = OUT / "staged_signals"
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 400})
W = 13.5 / 2.54
C_IN, C_DR5, INK2 = "#f47230", "#257de0", "#666666"

S = json.load(open(SIG / "summary.json"))
ga = pd.read_csv(HERE / "ga2020" / "fig4GH_digitized.csv")
V = pd.read_csv(SIG / "site_values_r7.csv")


def norm(v, t):
    return (np.asarray(v) - t["base"]) / (t["plateau"] - t["base"])


def stage_axis(ax, kmax):
    for k in range(-3, kmax + 1):
        ax.axvline(12 * k, color="#e6e6e6", lw=0.5, zorder=0)
        ax.text(12 * k + 5, 1.01, f"P{k}".replace("-", "−"), ha="center", va="bottom", fontsize=6.5, color=INK2,
                transform=ax.get_xaxis_transform())
    ax.axhline(0.5, color=INK2, lw=0.5, ls=":")
    ax.axhline(0, color="#bdbdbd", lw=0.5)
    ax.set_xlim(-39, 12 * kmax + 13)
    ax.set_ylim(-0.9, 2.05)
    ax.set_xlabel("Developmental time  τ = 12·k + h  (h)")




def draw(ax, tau, y, lo, hi, t, color, marker, label, dx):
    ax.errorbar(np.asarray(tau) + dx, y, yerr=[y - lo, hi - y], fmt="none", ecolor=color, elinewidth=0.6, alpha=0.45, capsize=0)
    ax.plot(np.asarray(tau) + dx, y, "-", color=color, lw=1.2)
    ax.plot(np.asarray(tau) + dx, y, marker, color=color, ms=3.6, mec="white", mew=0.5, label=label)
    ax.axvline(t["t50"], color=color, lw=0.8, ls="--")


fig = plt.figure(figsize=(W, W * 0.9))
top = fig.add_gridspec(1, 2, wspace=0.08, left=0.09, right=0.985, top=0.86, bottom=0.585)
axA, axB = fig.add_subplot(top[0, 0]), fig.add_subplot(top[0, 1])
axC = fig.add_subplot(fig.add_gridspec(1, 1, left=0.44, right=0.8, top=0.45, bottom=0.075)[0, 0])

# A: published
P = S["published"]["auxin"]
for panel, key, color, mk, lab, dx in (("G", "t50_in", C_IN, "o", "Auxin input (1 − qDII)", -0.6), ("H", "t50_dr5", C_DR5, "s", "DR5", 0.6)):
    d = ga[ga.panel == panel].assign(tau=lambda x: 12 * x.stage + x.hour).sort_values("tau")
    t = P[key]
    draw(axA, d.tau, norm(d["median"], t), norm(d.q1, t), norm(d.q3, t), t, color, mk, lab, dx)
stage_axis(axA, 1)
axA.set_ylabel("Rise, 0 = baseline, 1 = plateau")
axA.set_title("A  Published (GA2020 Fig 4G/H, N = 21)", fontsize=8.5, loc="left", pad=13)
axA.annotate("", xy=(P["t50_dr5"]["t50"], -0.55), xytext=(P["t50_in"]["t50"], -0.55),
             arrowprops=dict(arrowstyle="->", lw=0.7, color="#191919"))
axA.text((P["t50_in"]["t50"] + P["t50_dr5"]["t50"]) / 2, -0.5, f"{P['delay']:+.1f} h", ha="center", va="bottom", fontsize=7,
            bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))

# B: development group, exploratory main analysis
M = S["analyses"][0]
for col, key, color, mk, dx in (("c_lnq", "t50_in", C_IN, "o", -0.6), ("c_ndr5", "t50_dr5", C_DR5, "s", 0.6)):
    d = V.dropna(subset=[col])
    g = d.groupby(["k", "h"])
    c = g.agg(med=(col, "median"), q1=(col, lambda x: x.quantile(.25)), q3=(col, lambda x: x.quantile(.75)),
              n=(col, "size"), nm=("seq", "nunique")).reset_index()
    c = c[(c.n >= 5) & (c.nm >= 3)].assign(tau=lambda x: 12 * x.k + x.h).sort_values("tau")
    t = M[key]
    draw(axB, c.tau, norm(c.med, t), norm(c.q1, t), norm(c.q3, t), t, color, mk, None, dx)
stage_axis(axB, 2)
axB.set_yticklabels([])
axB.set_title("B  Development group, n = 14 (exploratory)", fontsize=8.5, loc="left", pad=13)
b = M["boot"]
axB.annotate("", xy=(M["t50_dr5"]["t50"], -0.55), xytext=(M["t50_in"]["t50"], -0.55),
             arrowprops=dict(arrowstyle="->", lw=0.7, color="#191919"))
axB.text((M["t50_in"]["t50"] + M["t50_dr5"]["t50"]) / 2, -0.5, f"{M['delay']:+.1f} h", ha="center", va="bottom", fontsize=7,
            bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none"))

from matplotlib.lines import Line2D
fig.legend([Line2D([], [], color=C_IN, marker="o", ms=3.6, mec="white", mew=0.5, lw=1.2),
            Line2D([], [], color=C_DR5, marker="s", ms=3.4, mec="white", mew=0.5, lw=1.2)],
           ["Auxin input (A: 1 − qDII; B: −ln qDII, site − reference)", "DR5 (A: $10^4$ a.u.; B: Normalized_DR5, site − reference)"],
           loc="upper center", bbox_to_anchor=(0.53, 1.0), ncol=2, frameon=False, fontsize=6.8, handlelength=2.2, columnspacing=1.5)
fig.text(0.53, 0.935, "Median per stage × hour, bars = interquartile range across meristems; dashed lines = t50",
         ha="center", fontsize=6.5, color=INK2)

# C: delays
rows = [("Published, 1 − qDII scale", S["published"]["auxin"]["delay"], None, None, "pub"),
        ("Published, −ln qDII scale", S["published"]["lnq"]["delay"], None, None, "pub"),
        ("Dev. group, authors' labels, published measure", S["bridge"]["authors' labels"]["delay"], None, None, "bridge"),
        ("Dev. group, Codex labels, published measure", S["bridge"]["Codex labels"]["delay"], None, None, "bridge")]
names = {"main: -ln qDII, Normalized DR5, contrast, r 7 um, T 12 h": "Main (exploratory): −ln qDII, DR5, contrast, T = 12 h",
         "T = 11.9 h": "T = 11.9 h (data median)", "T = 9.2 h": "T = 9.2 h", "T = 16.4 h": "T = 16.4 h",
         "without low-confidence labels": "Without low-confidence labels", "radius 10 um": "Radius 10 µm",
         "input 1 - qDII": "Input 1 − qDII", "output ln(DR5/TagBFP)": "Output ln(DR5/TagBFP)",
         "no reference subtraction": "No reference subtraction", "without DR5-TEST": "Without DR5-TEST",
         "cross-frame credible sites only": "Cross-frame credible sites only"}
for a in S["analyses"]:
    rows.append((names[a["name"]], a["delay"], a["boot"]["lo"], a["boot"]["hi"], "main" if a["name"].startswith("main") else "sens"))
y = np.arange(len(rows))[::-1].astype(float)
y[:4] += 0.6
y[:2] += 0.4
for yi, (lab, d, lo, hi, kind) in zip(y, rows):
    col = {"pub": "#191919", "bridge": INK2, "main": C_DR5, "sens": "#84b9f3"}[kind]
    if lo is not None:
        axC.plot([lo, hi], [yi, yi], "-", color=col, lw=1.6 if kind == "main" else 1.0, solid_capstyle="round")
    axC.plot(d, yi, "D" if kind == "pub" else "o", color=col, ms=4.2 if kind in ("pub", "main") else 3.4, mec="white", mew=0.5)
    axC.text(-0.02, yi, lab, ha="right", va="center", fontsize=6.6, transform=axC.get_yaxis_transform(),
             fontweight="bold" if kind in ("pub", "main") else "normal", color="#191919")
    axC.text(1.02, yi, f"{d:+.1f}" + (f"  [{lo:+.1f}, {hi:+.1f}]" if lo is not None else ""), ha="left", va="center",
             fontsize=6.4, color="#191919", transform=axC.get_yaxis_transform())
axC.axvline(0, color=INK2, lw=0.6)
axC.set_xlim(-10, 20)
axC.set_xticks([-8, -4, 0, 4, 8, 12, 16, 20])
axC.set_ylim(-0.8, y.max() + 0.8)
axC.set_yticks([])
axC.spines["left"].set_visible(False)
axC.set_xlabel("DR5 delay = t50(DR5) − t50(input)  (h)")
fig.text(0.01, 0.468, "C  Delay of the DR5 rise behind the input rise (bars: 95% bootstrap interval over meristems)", fontsize=8.5)
for ext in ("png", "pdf"):
    fig.savefig(OUT / f"fig_S1-3_staged_dr5_delay.{ext}")
print("saved")
