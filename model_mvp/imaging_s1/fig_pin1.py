"""Figure S1-1 (PIN1 centripetal polarity) and the corrected cell-to-cell PIN1 variation panel.

python fig_pin1.py        # needs out/pin1_polarity.json, out/model_v2_wall_asymmetry.json, out/model_validation.json
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial import Voronoi

import pin1_polarity as PP

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8, "axes.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "savefig.dpi": 400})
W = 13.5 / 2.54
C_PIN, C_PI, C_MOD = "#1b7837", "#7f7f7f", "#b2182b"
MAP_FRAME = "qDII-CLV3-PIN1-PI-LD_E37_171113_sam05_t00"
R_CLV3 = 27.3                                   # median CLV3-zone radius of the 21 qDII-DR5 meristems (calib_v2)


def short(frame):
    p = frame.split("_")
    return f"{p[1]} SAM{int(p[3][3:])}"


def cell_efflux_vectors(frame):
    """Per-cell net efflux vector from the cross-wall asymmetry: sum_w a_w (m_c - m_n)/(m_c + m_n) e_cw / sum_w a_w."""
    f = next(PP.DATA.rglob(frame + "_walls.csv"))
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
    g = pd.DataFrame(dict(cell=s.cell.values, ax=s.area.values * asym * e[:, 0], ay=s.area.values * asym * e[:, 1], a=s.area.values))
    v = g.groupby("cell").sum()
    pos = xy.loc[v.index].values - cen
    return pos, np.c_[v.ax / v.a, v.ay / v.a]


def panel_map(ax):
    pos, vec = cell_efflux_vectors(MAP_FRAME)
    r = np.hypot(pos[:, 0], pos[:, 1])
    vor = Voronoi(pos)
    for k in range(len(pos)):
        reg = vor.regions[vor.point_region[k]]
        if -1 in reg or not reg or r[k] > 52:
            continue
        poly = vor.vertices[reg]
        if np.hypot(poly[:, 0], poly[:, 1]).max() > 60:
            continue
        ax.fill(poly[:, 0], poly[:, 1], facecolor="#f4f4f4", edgecolor="#b8b8b8", lw=0.3)
    m = (r < 50) & (r > 3)
    inward = -(vec[:, 0] * pos[:, 0] + vec[:, 1] * pos[:, 1]) / np.maximum(r, 1e-9)
    n = np.maximum(np.hypot(vec[:, 0], vec[:, 1]), 1e-12)
    L = 4.6 * np.minimum(n / np.percentile(n[m], 90), 1.0)          # arrow length saturates at the 90th percentile
    u = vec / n[:, None] * L[:, None]
    q = ax.quiver(pos[m, 0], pos[m, 1], u[m, 0], u[m, 1], inward[m] / n[m], cmap="PuOr_r", clim=(-1, 1), angles="xy", scale_units="xy",
                  scale=1, width=0.0045, headwidth=3.2, headlength=3.4, headaxislength=3.0, minlength=0.5, pivot="mid")
    th = np.linspace(0, 2 * np.pi, 200)
    ax.plot(R_CLV3 * np.cos(th), R_CLV3 * np.sin(th), "--", color="k", lw=0.7)
    ax.plot([-50, -30], [-55, -55], color="k", lw=1.5)
    ax.text(-40, -53.5, "20 µm", ha="center", va="bottom")
    ax.set_xlim(-54, 54); ax.set_ylim(-59, 54); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"PIN1 net efflux direction, {short(MAP_FRAME)}", fontsize=8.5, pad=2)
    cb = plt.colorbar(q, ax=ax, orientation="horizontal", fraction=0.04, pad=0.01, shrink=0.55, ticks=[-1, 0, 1])
    cb.ax.set_xticklabels(["outward", "tangential", "inward"]); cb.outline.set_linewidth(0.4)


def paired(ax, recs, get, ylabel, title):
    for k, r in enumerate(recs):
        for sig, col, dx in (("PIN1", C_PIN, -0.13), ("PI", C_PI, 0.13)):
            d = get(r, sig)
            ax.errorbar(k + dx, d["mean"], yerr=[[d["mean"] - d["lo"]], [d["hi"] - d["mean"]]], fmt="o", ms=3.5, color=col, lw=0.8, capsize=1.5)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xticks(range(len(recs)), [short(r["frame"]) for r in recs], rotation=30, ha="right")
    ax.set_ylabel(ylabel); ax.set_title(title, fontsize=8.5)
    ax.plot([], [], "o", ms=3.5, color=C_PIN, label="PIN1"); ax.plot([], [], "o", ms=3.5, color=C_PI, label="PI (control)")


def fig_main():
    recs = json.load(open(OUT / "pin1_polarity.json"))["frames"]
    model = json.load(open(OUT / "model_v2_wall_asymmetry.json"))
    val = json.load(open(OUT / "model_validation.json"))
    fig = plt.figure(figsize=(W, W * 0.86))
    gs = fig.add_gridspec(2, 3, width_ratios=[1.0, 1.0, 1.0], height_ratios=[1.25, 1.0], hspace=0.55, wspace=0.78,
                          left=0.115, right=0.97, top=0.94, bottom=0.125)
    axA = fig.add_subplot(gs[0, :2]); panel_map(axA)
    axB = fig.add_subplot(gs[0, 2])
    paired(axB, recs, lambda r, s: r["main"]["I_" + s], "Centripetal index of\ncell polarity vector", "Pre-specified measure")
    axB.set_ylim(-0.01, 0.09)
    axC = fig.add_subplot(gs[1, 0])
    paired(axC, recs, lambda r, s: r["wall_asymmetry_detail"]["main"][s], "Cross-wall asymmetry", "Secondary measure")
    axC.legend(frameon=False, fontsize=7, loc="upper right", handletextpad=0.1, borderaxespad=0)
    axC.set_ylim(-0.03, 0.125)
    axD = fig.add_subplot(gs[1, 1])
    mid = [0.5 * (lo + hi) for lo, hi in PP.BANDS]
    for r in recs:
        b = r["wall_asymmetry_detail"]["bands"]
        axD.plot(mid, [x["PIN1"]["mean"] for x in b], "-o", ms=2.5, lw=0.8, color=C_PIN, alpha=0.85)
        axD.plot(mid, [x["PI"]["mean"] for x in b], "-o", ms=2.5, lw=0.8, color=C_PI, alpha=0.85)
    axD.axhline(0, color="k", lw=0.5); axD.axvline(R_CLV3, color="k", lw=0.6, ls="--")
    axD.set_xlabel("Distance from centre (µm)"); axD.set_ylabel("Cross-wall asymmetry"); axD.set_title("Radial profile", fontsize=8.5)
    axD.set_xticks([10, 20, 30, 40, 50]); axD.set_ylim(-0.03, 0.125)
    axE = fig.add_subplot(gs[1, 2])
    key = "frac_outer_side_higher"
    dat = [r["wall_asymmetry_detail"]["main"]["PIN1"][key] for r in recs]
    dpi = [r["wall_asymmetry_detail"]["main"]["PI"][key] for r in recs]
    mod = [m["main"]["PIN1"][key] for m in model]
    k0 = val["same, kappa_c = 0"][key]
    jit = lambda v: np.linspace(-0.12, 0.12, len(v))
    axE.plot(0 + jit(dat), dat, "o", ms=3.5, color=C_PIN)
    axE.plot(1 + jit(dpi), dpi, "o", ms=3.5, color=C_PI)
    axE.plot([2], [k0], "s", ms=3.5, color=C_MOD, mfc="none")
    axE.plot(3 + jit(mod), mod, "s", ms=3.5, color=C_MOD)
    axE.axhline(0.5, color="k", lw=0.5, ls=":")
    axE.set_xticks([0, 1, 2, 3], ["PIN1", "PI", "$\\kappa_c$=0", "$\\kappa_c$=1"])
    axE.text(0.5, -0.27, "Measured", transform=axE.get_xaxis_transform(), ha="center", va="top", fontsize=7.5)
    axE.text(2.5, -0.27, "Model", transform=axE.get_xaxis_transform(), ha="center", va="top", fontsize=7.5)
    axE.set_xlim(-0.5, 3.5); axE.set_ylim(0.3, 1.0)
    axE.set_ylabel("Fraction of radial walls\nwith outer side higher"); axE.set_title("Sign statistic", fontsize=8.5)
    for ax, s in ((axA, "A"), (axB, "B"), (axC, "C"), (axD, "D"), (axE, "E")):
        box = ax.get_subplotspec().get_position(fig)
        fig.text(box.x0 - (0.0 if ax is axA else 0.095), box.y1 + 0.012, s, fontsize=11, fontweight="bold", family="DejaVu Sans", va="bottom", ha="left")
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_S1-1_pin1_polarity.{ext}")
    plt.close(fig)


def fig_sigma():
    recs = json.load(open(OUT / "sigma_recheck.json"))
    fig, ax = plt.subplots(figsize=(W * 0.42, W * 0.42))
    fig.subplots_adjust(left=0.27, right=0.97, top=0.9, bottom=0.2)
    ax.axhspan(0.32, 0.48, color="#d0d0d0", lw=0)
    ax.text(0.5, 0.40, "Needed by the model\nfor the reported share\nof non-canonical angles", ha="center", va="center", fontsize=6.5, color="#404040")
    for x, key, col in ((0, "by_name", "#9ecae1"), (1, "corrected", "#0868ac")):
        v = [r[key]["sigma_PIN"] for r in recs]
        ax.plot(x + np.linspace(-0.12, 0.12, len(v)), v, "o", ms=3.5, color=col)
        ax.plot([x - 0.25, x + 0.25], [np.median(v)] * 2, color="k", lw=1)
        ax.text(x + 0.3, np.median(v), f"{np.median(v):.3f}", va="center", fontsize=7)
    ax.set_xticks([0, 1], ["Sides as\nnamed", "Sides\ncorrected"]); ax.set_xlim(-0.5, 1.75); ax.set_ylim(0, 0.55)
    ax.set_ylabel("Cell-to-cell PIN1 variation (log SD)"); ax.set_title("PIN1 variation, 4 meristems", fontsize=8.5)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_S1-1b_pin1_variation_corrected.{ext}")
    plt.close(fig)


if __name__ == "__main__":
    fig_main()
    fig_sigma()
