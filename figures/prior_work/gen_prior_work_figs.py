#!/usr/bin/env python3
"""Figures for the "已有工作积累" section of the thesis proposal (labels in English).

    python run_mech.py             # once: main-line run for the 3D view in Fig. 2A (mech.npz)
    python run_types.py            # once: three model runs for Fig. 2C-E (types.npz)
    python gen_prior_work_figs.py  # fig1_data.png, fig2_model.png, fig3_tests.png (+ .pdf)

Every number drawn here is read from files already in the repository:
  Fig. 1  reproductions/elife55832/outputs/nuclei_21/   (pipeline output, 21 meristems)
          model_mvp/calib_v2/out/measure_nuclei_21.json (cell spacing, CLV3 radius, P0 radius)
          model_mvp/noise_v3/out/pin1_measure.json       (cell-to-cell PIN1 spread, 4 meristems)
          model_mvp/noise_v3/RESULTS.md                  (sigma needed by the model: 0.32 / 0.48)
  Fig. 2  mech.npz (run_mech.py, frozen main line), types.npz (run_types.py),
          model_mvp/out/e11_grid.jsonl, model_mvp/out/e11_tau.jsonl
  Fig. 3  model_mvp/detuned_v3/out/{samples,calib,runs}.json (classification as in dv3_report.py)
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.text
import matplotlib.colors as mcolors
import matplotlib.patheffects as pe
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MM = ROOT / "model_mvp"
NUC = ROOT / "reproductions" / "elife55832" / "outputs" / "nuclei_21"
sys.path.insert(0, str(MM))
import analysis  # noqa: E402  (model_mvp/analysis.py: pattern statistics)

# Times-style serif, matching the Latin text in the proposal's own figure
SERIF = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]
plt.rcParams.update({
    "font.family": SERIF, "mathtext.fontset": "custom", "mathtext.rm": "Liberation Serif",
    "mathtext.it": "Liberation Serif:italic", "mathtext.bf": "Liberation Serif:bold", "mathtext.fallback": "stix",
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300,
})
INK, GREY, LIGHT = "#1A1A1A", "#8C8C8C", "#D0D0D0"

# FIG_LANG=zh python gen_prior_work_figs.py  -> Chinese labels (Song-style CJK + Times-style Latin), files *_zh.*
ZH = os.environ.get("FIG_LANG", "en") == "zh"
SUFFIX = "_zh" if ZH else ""
CJK_FONT = "Noto Serif CJK SC"
if ZH:
    plt.rcParams.update({"font.family": ["Times New Roman", "Liberation Serif", "SimSun", CJK_FONT],
                         "mathtext.rm": CJK_FONT})

TR = {
    "Auxin input (1 − $\\mathit{qDII}$)": "生长素输入（1 − $\\mathit{qDII}$）",
    "$\\mathit{DR5}$ output": "$\\mathit{DR5}$转录输出",
    "low": "低", "high": "高",
    "L1 nuclear\nspacing": "L1层细胞核\n最近邻间距", "Distance (µm)": "距离（µm）",
    "$\\mathit{CLV3}$ zone\nradius": "$\\mathit{CLV3}$表达区\n半径", "P0 radius\n(0 h)": "P0距中心\n（0 h）",
    "Radius (µm)": "半径（µm）",
    "Needed by the model\nto match observed\nirregularity": "模型再现实测\n不规则性所需",
    "Measured\n(4 meristems)": "实测\n（4个茎尖）",
    "Cell-to-cell PIN1 variation\n(log SD)": "细胞间PIN1差异\n（对数标准差）",
    "PIN1 variation": "PIN1量的细胞间差异",
    "Central zone": "中央区", "Competent\nring": "发生环", "Primordium": "原基", "L1\nepidermis": "L1层",
    "Inner\nlayer*": "内层*", "Vascular\nstrand*": "维管束*",
    "Peripheral\nsynthesis*": "外围\n合成*", "Auxin $A$": "生长素 $A$", "epidermis": "表皮层",
    "PIN1 polarity": "PIN1极性", "up-gradient": "朝高浓度",
    "$\\mathit{DR5}$-like $R$": "$\\mathit{DR5}$样读出 $R$", "passive read-out": "被动读出",
    "Integration $M$": "时间整合 $M$", "leaky, $\\tau_M$": "泄漏积分，$\\tau_M$",
    "Secondary\ninhibition": "次级\n抑制", "Initiation": "原基启动", "$M \\geq \\theta$ in ring": "环内 $M \\geq \\theta$",
    "placed object": "放置的对象", "Inner layer*": "内层*", "vascular drainage": "维管排出",
    "inward*": "向内*", "polarizes": "定极性", "transport": "运输", "places": "放置", "drains": "排出",
    "sink": "汇", "polarity\ncue": "极化\n线索", "triggers": "触发", "raises θ": "抬高θ",
    "Auxin (model)": "模型生长素浓度",
    "Ring mid-radius / primordium range": "发生环中线半径 / 原基作用范围",
    "Divergence angle (°)": "相邻原基夹角（°）",
    "Distichous": "二列互生", "Spiral": "螺旋", "Decussate": "交互对生", "Irregular": "不规则",
    "Integration time constant / plastochron": "积分时间常数 / 叶间期",
    "Fraction of regular spirals": "规则螺旋所占比例",
    "Regular spiral": "出现规则螺旋", "Initiates without transport": "无运输也能起始",
    "Primordium range $w$ (cells)": "原基作用范围 $w$（细胞）",
    "Centripetal transport bias $\\kappa_\\mathrm{c}$": "向心运输偏置 $\\kappa_\\mathrm{c}$",
    "Mean divergence (°)": "平均发散角（°）", "P1–P5 spread (°)": "P1—P5夹角离散（°）",
    "Plastochron (h)": "发生间隔（h）", "Co-initiation (%)": "同时起始比例（%）",
    "All runs": "全部运行", "Regular\nspirals": "规则\n螺旋",
}
TR_RE = [
    (r"^(\d+) meristems$", r"\1个茎尖"),
    (r"^(\d+) meristems \(P0: (\d+)\)$", r"\1个茎尖（P0：\2个）"),
    (r"^Subcritical \(n = (\d+)\)$", r"不能自发成峰（n = \1）"),
    (r"^Supercritical \(n = (\d+)\)$", r"能自发成峰（n = \1）"),
]
TYPE_ZH = {"Distichous": "二列互生", "Spiral": "螺旋", "Decussate": "交互对生"}


def tr(s):
    """Chinese label for an English one (identity when FIG_LANG is not zh)."""
    if not ZH:
        return s
    if s in TR:
        return TR[s]
    for pat, rep in TR_RE:
        if re.match(pat, s):
            return re.sub(pat, rep, s)
    m = re.match(r"^(Distichous|Spiral|Decussate) (\(\$R_\\mathrm\{c\}\$ = [\d.]+\))\n(.*)$", s)
    if m:
        sub = re.sub(r"^dominant angle (\d+)°$", r"主导夹角\1°", m.group(3))
        sub = re.sub(r"^pairs, (\d+)° between nodes$", r"每节2个原基，相邻两节转\1°", sub)
        return f"{TYPE_ZH[m.group(1)]}（{m.group(2)[1:-1]}）\n{sub}"
    return s


def has_cjk(s):
    return any("一" <= ch <= "鿿" or "＀" <= ch <= "￯" for ch in s)


def localize(fig):
    """Translate every text in the figure; texts that mix mathtext and Chinese get the CJK font."""
    if not ZH:
        return
    for t in fig.findobj(matplotlib.text.Text):
        old = t.get_text()
        new = tr(old)
        if new != old:
            t.set_text(new)
        if "$" in new and has_cjk(new):
            t.set_fontfamily(CJK_FONT)
BLUE, GREEN, ORANGE, RED = "#0072B2", "#009E73", "#D55E00", "#C0392B"
TYPE_COL = {"distichous": BLUE, "intermediate": "#56B4E9", "spiral": GREEN, "decussate": ORANGE}
OUTLINE = [pe.withStroke(linewidth=1.2, foreground="black")]
LETTER = dict(fontsize=10, fontweight="bold", family=["Liberation Sans", "DejaVu Sans"])


def panel_letter(ax, s, dx=-0.02, dy=1.02):
    ax.text(dx, dy, s, transform=ax.transAxes, va="bottom", ha="right", **LETTER)


def voronoi_cells(x, y, rmax):
    """Voronoi polygons of the points, clipped to a disc of radius rmax (ghost ring outside)."""
    k = np.arange(96) * 2 * np.pi / 96
    ghost = np.c_[1.25 * rmax * np.cos(k), 1.25 * rmax * np.sin(k)]
    vor = Voronoi(np.vstack([np.c_[x, y], ghost]))
    polys = []
    for i in range(len(x)):
        poly = vor.vertices[vor.regions[vor.point_region[i]]]
        r = np.hypot(poly[:, 0], poly[:, 1])
        polys.append(poly * np.minimum(1.0, rmax / np.maximum(r, 1e-9))[:, None])
    return polys


def low_high_bar(fig, pc, rect, label=None):
    cax = fig.add_axes(rect)
    cb = plt.colorbar(pc, cax=cax, orientation="horizontal")
    cb.set_ticks(pc.get_clim()); cb.set_ticklabels([tr("low"), tr("high")]); cb.outline.set_linewidth(0.4)
    cax.tick_params(length=0, pad=1.5, labelsize=6.5)
    if label:
        cax.set_xlabel(label, fontsize=7, labelpad=1)
    return cax


# ---------------------------------------------------------------- Fig. 1: data
EXAMPLE = "qDII-DR5-CLV3-LD_E25_170811_sam04"
RMAX = 55.0


def load_sam(name, frame="t00"):
    d = NUC / name / name / f"{name}_{frame}"
    rows = list(csv.DictReader(open(d / f"{name}_{frame}_aligned_L1_normalized_signal_data.csv")))
    get = lambda k: np.array([float(r[k]) for r in rows])
    sig = dict(x=get("aligned_x"), y=get("aligned_y"), auxin=get("Normalized_Auxin"), dr5=get("Normalized_DR5"),
               clv3_r=float(rows[0]["clv3_radius"]))
    prim = {}
    for r in csv.DictReader(open(d / f"{name}_{frame}_aligned_primordia_extrema.csv")):
        if r["extremum_type"] == "minimum":                 # qDII minimum = auxin-input maximum
            prim[int(r["primordium"])] = (float(r["aligned_x"]), float(r["aligned_y"]))
    return sig, prim


def sam_map(ax, sig, prim, key, cmap, show=(0, 1, 2)):
    keep = np.hypot(sig["x"], sig["y"]) < RMAX + 4
    x, y, v = sig["x"][keep], sig["y"][keep], sig[key][keep]
    lo, hi = np.percentile(v, [2, 98])
    pc = PolyCollection(voronoi_cells(x, y, RMAX), array=v, cmap=cmap, edgecolors="#00000040", linewidths=0.2)
    pc.set_clim(lo, hi)
    ax.add_collection(pc)
    ax.add_patch(plt.Circle((0, 0), sig["clv3_r"], fill=False, ec="white", ls=(0, (4, 2)), lw=1.0))
    for k in show:
        if k in prim:
            px, py = prim[k]
            ax.plot(px, py, "o", ms=11, mfc="none", mec="white", mew=1.0)
            ax.text(px, py + 7.0, f"P{k}", color="white", ha="center", va="bottom", fontsize=8.5, fontweight="bold",
                    path_effects=OUTLINE)
    # scale bar in the empty lower-left corner, outside the disc
    ax.plot([-RMAX + 1, -RMAX + 21], [-RMAX + 1.5, -RMAX + 1.5], color=INK, lw=1.6, solid_capstyle="butt")
    ax.text(-RMAX + 11, -RMAX + 3.5, "20 µm", color=INK, ha="center", va="bottom", fontsize=7.5)
    ax.set_xlim(-RMAX, RMAX); ax.set_ylim(-RMAX, RMAX); ax.set_aspect("equal"); ax.axis("off")
    return pc


def fig1():
    meas = json.load(open(MM / "calib_v2" / "out" / "measure_nuclei_21.json"))
    pin = json.load(open(MM / "noise_v3" / "out" / "pin1_measure.json"))
    sig, prim = load_sam(EXAMPLE)

    # explicit layout in inches, so that the maps span exactly the width of the bottom row
    W, H = 6.3, 6.05
    XL, XR, GAP = 0.08, 6.22, 0.14                 # outer left / right edge shared by both rows
    S = (XR - XL - GAP) / 2                         # map size
    BY, BH = 0.48, 1.5                              # bottom row: axes bottom and height
    MY = 2.78                                       # maps: bottom edge
    fig = plt.figure(figsize=(W, H))
    box = lambda x, y, w, h: [x / W, y / H, w / W, h / H]

    for c, (key, cmap, title) in enumerate((("auxin", "viridis", "Auxin input (1 − $\\mathit{qDII}$)"),
                                             ("dr5", "magma", "$\\mathit{DR5}$ output"))):
        x0 = XL + c * (S + GAP)
        ax = fig.add_axes(box(x0, MY, S, S))
        pc = sam_map(ax, sig, prim, key, cmap)
        ax.set_title(title, pad=2, fontsize=9)
        low_high_bar(fig, pc, box(x0 + 0.24 * S, MY - 0.2, 0.52 * S, 0.06))
        fig.text(x0 / W, (MY + S) / H, "AB"[c], va="top", ha="left", **LETTER)

    rng = np.random.default_rng(0)
    d = np.array([m["d"] for m in meas])
    clv = np.array([m["clv3_radius"] for m in meas])
    p0 = np.array([m["p0_radius_t00"] for m in meas if m.get("p0_radius_t00") is not None])

    def strip(ax, xpos, vals, col):
        ax.scatter(xpos + rng.uniform(-0.13, 0.13, len(vals)), vals, s=10, color=col, alpha=0.85, lw=0, zorder=3)
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        ax.plot([xpos - 0.26, xpos + 0.26], [med, med], color=INK, lw=1.2, zorder=4)
        ax.plot([xpos, xpos], [q1, q3], color=INK, lw=0.8, zorder=4)

    cols = [(0.62, 0.95, "C"), (2.18, 1.62, "D"), (XR - 1.6, 1.6, "E")]   # (left, width) of each bottom axes
    letter_x = [XL, 1.72, 3.98]

    ax = fig.add_axes(box(cols[0][0], BY, cols[0][1], BH))
    strip(ax, 0, d, GREY)
    ax.set_xticks([0]); ax.set_xticklabels([tr("L1 nuclear\nspacing")]); ax.set_xlim(-0.6, 0.6)
    ax.set_ylabel("Distance (µm)"); ax.set_ylim(4.2, 4.85)
    ax.text(0.33, np.median(d), f"{np.median(d):.2f}", va="center", fontsize=7)
    ax.set_title(f"{len(d)} meristems", pad=3)

    ax = fig.add_axes(box(cols[1][0], BY, cols[1][1], BH))
    strip(ax, 0, clv, GREEN); strip(ax, 1, p0, ORANGE)
    ax.set_xticks([0, 1]); ax.set_xticklabels([tr("$\\mathit{CLV3}$ zone\nradius"), tr("P0 radius\n(0 h)")]); ax.set_xlim(-0.6, 1.6)
    ax.set_ylabel("Radius (µm)"); ax.set_ylim(10, 45)
    for xpos, vals in ((0, clv), (1, p0)):
        ax.text(xpos + 0.33, np.median(vals), f"{np.median(vals):.1f}", va="center", fontsize=7)
    ax.set_title(f"{len(clv)} meristems (P0: {len(p0)})", pad=3)

    ax = fig.add_axes(box(cols[2][0], BY, cols[2][1], BH))
    sp = np.array([p["sigma_PIN"] for p in pin])
    ax.axhspan(0.32, 0.48, color=LIGHT, lw=0, zorder=0)
    ax.text(0.5, 0.40, "Needed by the model\nto match observed\nirregularity", ha="center", va="center", fontsize=6.5,
            color="#444444", transform=ax.get_yaxis_transform())
    ax.scatter(rng.uniform(-0.12, 0.12, len(sp)) + 0.5, sp, s=14, color=BLUE, zorder=3, lw=0)
    ax.plot([0.25, 0.75], [np.median(sp)] * 2, color=INK, lw=1.2)
    ax.text(0.8, np.median(sp), f"{np.median(sp):.2f}", va="center", fontsize=7)
    ax.set_xlim(0, 1); ax.set_xticks([0.5]); ax.set_xticklabels([tr("Measured\n(4 meristems)")])
    ax.set_ylim(0, 0.55); ax.set_ylabel("Cell-to-cell PIN1 variation\n(log SD)")
    ax.set_title("PIN1 variation", pad=3)

    for lx, (_, _, s) in zip(letter_x, cols):
        fig.text(lx / W, (BY + BH + 0.26) / H, s, va="top", ha="left", **LETTER)

    save(fig, "fig1_data", tight=False)


# ---------------------------------------------------------------- Fig. 2: model
TYPES = [("distichous", "Distichous", 2.5), ("spiral", "Spiral", 3.5), ("decussate", "Decussate", 6.0)]


def model_map(ax, z, name):
    par = json.loads(str(z[f"{name}_par"]))
    pts, A, pin, prim = z[f"{name}_pts"], z[f"{name}_A"], z[f"{name}_pin"], z[f"{name}_prim"]
    R = par["R_out"]
    pc = PolyCollection(voronoi_cells(pts[:, 0], pts[:, 1], R), array=A, cmap="viridis", edgecolors="#00000030",
                        linewidths=0.15)
    pc.set_clim(0, np.percentile(A, 99.5))
    ax.add_collection(pc)
    ax.quiver(pts[:, 0], pts[:, 1], pin[:, 0], pin[:, 1], color="white", scale=30, width=0.004, headwidth=4,
              headlength=4, alpha=0.85)
    for (x, y, i, age) in prim:
        if np.hypot(x, y) < R - 0.5:
            ax.add_patch(plt.Circle((x, y), par["w"], fill=False, ec="white", lw=0.8))
    for r in (par["R_c"], par["R_p"]):
        ax.add_patch(plt.Circle((0, 0), r, fill=False, ec=RED, ls=(0, (3, 2)), lw=0.7))
    ax.set_xlim(-R, R); ax.set_ylim(-R, R); ax.set_aspect("equal"); ax.axis("off")
    return pc


# ---------------------------------------------------------------- Fig. 2A: shoot apex seen obliquely, narrow wedge cut away
HD, BUMP, T1, T2, ELEV, WEDGE = 8.0, 4.2, 1.25, 1.6, 45, 70   # dome height, bulge, L1 / inner-layer thickness, view, cut


def ccw(poly):
    """Counter-clockwise vertex order, so that every face normal points up (consistent shading)."""
    x, y = poly[:, 0], poly[:, 1]
    return poly if np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)) > 0 else poly[::-1]


def clip_half(poly, n):
    """Part of a polygon with dot(p, n) <= 0 (half-plane through the origin)."""
    if poly is None:
        return None
    out = []
    for k in range(len(poly)):
        P, Q = poly[k], poly[(k + 1) % len(poly)]
        dp, dq = P @ n, Q @ n
        if dp <= 0:
            out.append(P)
        if (dp <= 0) != (dq <= 0):
            out.append(P + dp / (dp - dq) * (Q - P))
    return np.array(out) if len(out) >= 3 else None


def mech_3d(ax, m):
    """Dome-shaped apex on a base plane: surface colour and PIN1 arrows from one main-line run (run_mech.py);
    the dome and the primordium bulges are schematic (the model itself is flat)."""
    from matplotlib.colors import LightSource, Normalize
    from mpl_toolkits.mplot3d import proj3d
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from scipy.spatial import cKDTree

    par = json.loads(str(m["par"]))
    R, w = par["R_out"], par["w"]
    pts, A, A2, pin, prim = m["pts"], m["A"], m["A2"], m["pin"], m["prim"]
    inside = [p for p in prim if np.hypot(p[0], p[1]) < R - 0.5]

    def surf(x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        z = HD * (1.0 - np.clip(np.hypot(x, y) / R, 0, 1) ** 2) ** 0.85
        for (px, py, _, age) in inside:                     # older primordia bulge more
            wb = w * (0.8 + age / 40.0)
            z = z + BUMP * (1 - np.exp(-age / 14.0)) * np.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * wb ** 2))
        return z

    # narrow wedge cut away between d1 (through a young primordium) and d2
    sec = min([p for p in inside if p[3] >= 6], key=lambda p: p[3])
    d1 = sec[:2] / np.hypot(sec[0], sec[1])
    perp = lambda d: np.array([-d[1], d[0]])
    rot = lambda d, a: np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)])
    best = None
    for sgn in (1, -1):
        d2 = rot(d1, sgn * np.radians(WEDGE))
        n1, n2 = perp(d1) * np.sign(perp(d1) @ d2), perp(d2) * np.sign(perp(d2) @ d1)   # normals into the wedge
        score = sum(p[3] for p in inside if not (p[:2] @ n1 > 0 and p[:2] @ n2 > 0))
        if best is None or score > best[0]:
            best = (score, d2, n1, n2)
    _, d2, n1, n2 = best
    vb = (d1 + d2) / np.hypot(*(d1 + d2))
    look = vb + 0.35 * n1                                   # turn a little towards the face with the strand
    az = np.degrees(np.arctan2(look[1], look[0]))

    ax.computed_zorder = False
    light = LightSource(azdeg=az + 60, altdeg=60)
    nt = Normalize(0, np.percentile(A, 99.5))
    nb = Normalize(np.percentile(A2, 1), np.percentile(A2, 99))
    viridis = plt.get_cmap("viridis")

    th = np.linspace(0, 2 * np.pi, 121)                     # soft shadow on the base plane
    sh = Poly3DCollection([np.c_[1.06 * R * np.cos(th), 1.06 * R * np.sin(th), np.full_like(th, -0.05)]],
                          facecolors=(0, 0, 0, 0.07), edgecolors="none")
    sh.set_zorder(0); ax.add_collection3d(sh)

    faces, cols = [], []
    for poly, a in zip(voronoi_cells(pts[:, 0], pts[:, 1], R), A):
        poly = ccw(poly)
        for piece in (clip_half(poly, n1), clip_half(clip_half(poly, -n1), n2)):   # polygon minus the wedge
            if piece is not None:
                faces.append(np.c_[piece, surf(piece[:, 0], piece[:, 1])]); cols.append(viridis(nt(a)))
    ps = Poly3DCollection(faces, facecolors=cols, edgecolors=(0, 0, 0, 0.07), linewidths=0.1, shade=True,
                          lightsource=light)
    ps.set_zorder(2); ax.add_collection3d(ps)

    rng = np.random.default_rng(5)                          # PIN1 polarity on a quarter of the cells
    mag = np.hypot(pin[:, 0], pin[:, 1])
    keep = (mag > 0.3) & (np.hypot(pts[:, 0], pts[:, 1]) < R - 1.5) & (rng.random(len(mag)) < 0.25)
    keep &= ~((pts @ n1 > -1.5) & (pts @ n2 > -1.5))         # stay clear of the cut
    x, y = pts[keep, 0], pts[keep, 1]
    du, dv = 1.2 * pin[keep, 0] / mag[keep], 1.2 * pin[keep, 1] / mag[keep]
    z0 = surf(x, y) + 0.12
    ax.quiver(x, y, z0, du, dv, surf(x + du, y + dv) + 0.12 - z0, color=(1, 1, 1, 0.9), lw=0.55,
              arrow_length_ratio=0.45, zorder=3)
    for r in (par["R_c"], par["R_p"]):                      # competent ring
        cx, cy = r * np.cos(np.linspace(0, 2 * np.pi, 361)), r * np.sin(np.linspace(0, 2 * np.pi, 361))
        cut = (np.c_[cx, cy] @ n1 > 0) & (np.c_[cx, cy] @ n2 > 0)
        cx, cy = np.where(cut, np.nan, cx), np.where(cut, np.nan, cy)
        ax.plot(cx, cy, surf(np.nan_to_num(cx), np.nan_to_num(cy)) + 0.15, color=RED, lw=0.9, ls=(0, (3, 2)), zorder=3)

    # cut faces drawn as a tissue section: L1 cells (auxin colour; walls where the cut crosses the surface cells),
    # the inner layer, deeper tissue (schematic cells, lighter near the top) and a vascular strand of elongated cells
    from scipy.spatial import Voronoi
    tree = cKDTree(pts)
    s = np.linspace(0, R, 401)
    sp = float(np.hypot(sec[0], sec[1]))                     # the cut primordium (on face d1)
    zt = float(surf(sp * d1[0], sp * d1[1]))
    half = 0.95                                             # half-width of the vascular strand
    to3 = lambda d, P: np.c_[P[:, 0] * d[0], P[:, 0] * d[1], P[:, 1]]
    lerp = lambda c0, c1, f: tuple(np.array(mcolors.to_rgb(c0)) * (1 - f) + np.array(mcolors.to_rgb(c1)) * f)

    def deep_cells(g, rng):
        """Voronoi cells (jittered grid seeds) filling 0 <= z <= g(s) on one face, as (s, z) polygons."""
        h = 1.2
        seeds = [((i + 0.5 + rng.uniform(-0.32, 0.32)) * h, (j + 0.5 + rng.uniform(-0.32, 0.32)) * h)
                 for i in range(int(R / h) + 1) for j in range(int((HD + BUMP) / h) + 1)]
        seeds = np.array([q for q in seeds if q[1] < np.interp(q[0], s, g) + 0.4])
        far = np.array([[-50, -50], [-50, 80], [80, -50], [80, 80]])
        vor = Voronoi(np.r_[seeds, far])
        out = []
        for k in range(len(seeds)):
            reg = vor.regions[vor.point_region[k]]
            if -1 in reg or not reg:
                continue
            P = vor.vertices[reg]
            P = P[np.argsort(np.arctan2(P[:, 1] - seeds[k, 1], P[:, 0] - seeds[k, 0]))]
            for n_, c_ in (((-1.0, 0.0), 0.0), ((1.0, 0.0), R), ((0.0, -1.0), 0.0)):   # box: 0 <= s <= R, z >= 0
                n_ = np.array(n_)
                P = clip_half(P - n_ * c_, n_)                     # keep n.p <= c
                if P is None:
                    break
                P = P + n_ * c_
            if P is None:
                continue
            Q = np.vstack([np.linspace(P[i], P[(i + 1) % len(P)], 12, endpoint=False) for i in range(len(P))])
            Q[:, 1] = np.minimum(Q[:, 1], np.interp(Q[:, 0], s, g))        # trim to the tissue below the inner layer
            area = 0.5 * abs(np.dot(Q[:, 0], np.roll(Q[:, 1], 1)) - np.dot(Q[:, 1], np.roll(Q[:, 0], 1)))
            if area > 0.04:
                out.append((Q, seeds[k]))
        return out

    rng_c = np.random.default_rng(11)
    Ld = np.array(light.direction[:2]); Ld /= np.hypot(*Ld)
    for d, nf in ((d1, n1), (d2, n2)):
        lit = 0.9 + 0.1 * max(float(nf @ Ld), 0.0)              # the two faces catch the light differently
        dim = lambda c: tuple(np.array(mcolors.to_rgba(c)[:3]) * lit) + (1.0,)
        X, Y = s * d[0], s * d[1]
        Zs = surf(X, Y)
        g = np.maximum(Zs - T1 - T2, 0)
        _, idx = tree.query(np.c_[X, Y] - 0.15 * nf)           # surface cell just beside the cut
        polys, fc, ec = [], [], []
        brk = np.r_[0, np.where(np.diff(idx) != 0)[0] + 1, len(s) - 1]
        for a, b in zip(brk[:-1], brk[1:]):
            seg = slice(a, b + 1)
            top_, mid_, bot_ = Zs[seg], np.maximum(Zs[seg] - T1, 0), g[seg]
            polys.append(np.r_[np.c_[s[seg], top_], np.c_[s[seg], mid_][::-1]])          # L1 cell
            fc.append(viridis(nt(A[idx[a]]))); ec.append((0.12, 0.12, 0.12, 0.55))
            polys.append(np.r_[np.c_[s[seg], mid_], np.c_[s[seg], bot_][::-1]])          # inner-layer cell
            fc.append(lerp("#DCE3EA", "#B9C6D3", nb(A2[idx[a]]) * 0.6)); ec.append("#7D8C9B")
        for Q, c in deep_cells(g, rng_c):
            f = np.clip(c[1] / max(np.interp(c[0], s, g), 1e-6), 0, 1)                   # 1 near the top
            polys.append(Q); fc.append(lerp("#E3D4BF", "#F7F1E7", f)); ec.append("#B8A68D")
        pc = Poly3DCollection([to3(d, P) for P in polys], facecolors=[dim(c) for c in fc], edgecolors=ec,
                              linewidths=0.3)
        pc.set_zorder(5); ax.add_collection3d(pc)
        ax.plot(X, Y, Zs, color=INK, lw=0.9, zorder=6)
        ax.plot(X, Y, np.maximum(Zs - T1, 0), color="#2B2B2B", lw=0.45, zorder=6)
        ax.plot(X, Y, g, color="#55606B", lw=0.45, zorder=6)
        ax.plot([0, X[-1]], [0, Y[-1]], [0, 0], color=INK, lw=0.5, zorder=6)
        ax.plot([X[-1]] * 2, [Y[-1]] * 2, [0, Zs[-1]], color=INK, lw=0.5, zorder=6)
    ax.plot([0, 0], [0, 0], [float(surf(0, 0)), 0], color=INK, lw=0.6, zorder=6)

    # vascular strand under the cut primordium: three files of long, narrow (provascular-like) cells
    zs_top = zt - T1 - T2
    cells_v, nfile, hgt = [], 3, 1.75
    for c in range(nfile):
        s0, s1 = sp - half + 2 * half * c / nfile, sp - half + 2 * half * (c + 1) / nfile
        z = zs_top
        first = hgt * (0.45 + 0.3 * c)                      # stagger the files
        while z > 0:
            z0 = max(z - (first if z == zs_top else hgt), 0.0)
            cells_v.append(np.array([[s0, z], [s1, z], [s1, z0], [s0, z0]]))
            z = z0
    fcv = [lerp("#E8B96E", "#F4D9A8", min(P[:, 1].mean() / max(zs_top, 1e-6), 1)) for P in cells_v]
    vq = Poly3DCollection([to3(d1, P) for P in cells_v], facecolors=fcv, edgecolors="#9A7136", linewidths=0.35)
    vq.set_zorder(7); ax.add_collection3d(vq)
    ax.plot(*to3(d1, np.array([[sp - half, zs_top], [sp - half, 0]])).T, color="#7A5524", lw=0.6, zorder=7)
    ax.plot(*to3(d1, np.array([[sp + half, zs_top], [sp + half, 0]])).T, color="#7A5524", lw=0.6, zorder=7)
    ax.plot([sp * d1[0]] * 2, [sp * d1[1]] * 2, [zt - 0.2, zs_top + 0.35], color=INK, lw=0.9,
            ls=(0, (2.5, 1.5)), zorder=8)
    ax.quiver(sp * d1[0], sp * d1[1], zs_top + 1.3, 0, 0, -1.1, color=INK, lw=0.9, arrow_length_ratio=0.8, zorder=8)
    ax.quiver(sp * d1[0], sp * d1[1], 0.55 * zs_top, 0, 0, -0.3 * zs_top, color="white", lw=1.1,
              arrow_length_ratio=0.35, zorder=8)

    lim = R + 0.6
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim); ax.set_zlim(0, HD + BUMP)
    ax.set_box_aspect((2 * lim, 2 * lim, HD + BUMP), zoom=1.12)
    ax.view_init(elev=ELEV, azim=az)
    ax.set_axis_off()

    # six labels, each placed outward from the apex with a short leader
    def p2(xyz):
        a_, b_, _ = proj3d.proj_transform(*xyz, ax.get_proj())
        return np.array([a_, b_])

    def on_cut(d, q, depth):
        return (q * d[0], q * d[1], float(surf(q * d[0], q * d[1])) - depth)

    def on_surf(P):
        return (P[0], P[1], float(surf(P[0], P[1])))

    behind = [p for p in inside if p is not sec and not (p[:2] @ n1 > 0 and p[:2] @ n2 > 0)]
    older = max(behind, key=lambda p: p[3]) if behind else sec
    rr = 0.5 * (par["R_c"] + par["R_p"])
    angs = np.radians(np.arange(0, 360, 3))
    ring_pts = [rr * np.array([np.cos(a), np.sin(a)]) for a in angs]
    ring_pts = [P for P in ring_pts if not (P @ n1 > -1 and P @ n2 > -1)]
    ring_l = min(ring_pts, key=lambda P: p2(on_surf(P))[0])          # leftmost visible point of the ring
    top = p2(on_surf((0.0, 0.0)))
    ax.annotate("Central zone", xy=top, xycoords="data", xytext=(0, 50), textcoords="offset points", ha="center",
                va="bottom", fontsize=6.8, arrowprops=dict(arrowstyle="-", lw=0.5, color=INK, shrinkA=1.5, shrinkB=0),
                zorder=10)
    items = [("Competent\nring", on_surf(ring_l)),
             ("Primordium", on_surf(older[:2])),
             ("L1\nepidermis", on_cut(d1, 0.86 * R, T1 / 2)),
             ("Inner\nlayer*", on_cut(d1, 0.25 * R, T1 + T2 / 2)),
             ("Vascular\nstrand*", (sp * d1[0], sp * d1[1], 0.3 * (zt - T1 - T2)))]
    c0 = p2((0, 0, 0.5 * HD))[0]
    for side in "LR":                                       # two columns, ordered by height: leaders do not cross
        col = sorted([it for it in items if (p2(it[1])[0] < c0) == (side == "L")], key=lambda it: -p2(it[1])[1])
        ys = np.linspace(0.86, 0.14, len(col)) if len(col) > 1 else [0.62]
        for (text, xyz), yt in zip(col, ys):
            ax.annotate(text, xy=p2(xyz), xycoords="data", xytext=(0.0 if side == "L" else 1.0, yt),
                        textcoords="axes fraction", ha="left" if side == "L" else "right", va="center", fontsize=6.8,
                        linespacing=1.0, arrowprops=dict(arrowstyle="-", lw=0.5, color=INK, shrinkA=1.5, shrinkB=0),
                        zorder=10)


def loop_panel(ax):
    """Panel B: regulatory loop of the model (after the layout of the earlier schematic, simplified)."""
    from matplotlib.patches import FancyBboxPatch
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    BW, BH = 0.235, 0.125
    XL, XM, XR = 0.125, 0.49, 0.85
    Y = [0.85, 0.665, 0.48, 0.295, 0.11]
    nodes = {
        "src": (XL, Y[0], "Peripheral\nsynthesis*", None, "solid"),
        "A": (XM, Y[0], "Auxin $A$", "epidermis", "solid"),
        "pin": (XR, Y[0], "PIN1 polarity", "up-gradient", "solid"),
        "dr5": (XL, Y[1], "$\\mathit{DR5}$-like $R$", "passive read-out", "solid"),
        "M": (XM, Y[1], "Integration $M$", "leaky, $\\tau_M$", "solid"),
        "inh": (XL, Y[2], "Secondary\ninhibition", None, "solid"),
        "ini": (XM, Y[2], "Initiation", "$M \\geq \\theta$ in ring", "solid"),
        "pri": (XM, Y[3], "Primordium", None, "solid"),
        "inner": (XM, Y[4], "Inner layer*", "vascular drainage", "solid"),
    }
    for key, (x, y, title, sub, style) in nodes.items():
        fc = "#E6E6E6" if style == "state" else "white"
        ec = GREY if style == "grey" else INK
        ls = (0, (3, 1.5)) if style == "dashed" else "solid"
        ax.add_patch(FancyBboxPatch((x - BW / 2, y - BH / 2), BW, BH, boxstyle="round,pad=0,rounding_size=0.02",
                                    fc=fc, ec=ec, lw=1.3 if style == "state" else 0.8, ls=ls))
        tc = "#555555" if style == "grey" else INK
        if sub:
            ax.text(x, y + 0.022, title, ha="center", va="center", fontsize=7.0, color=tc)
            ax.text(x, y - 0.03, sub, ha="center", va="center", fontsize=6.0, color=tc)
        else:
            ax.text(x, y, title, ha="center", va="center", fontsize=7.0, color=tc, linespacing=1.0)

    L, Rt = lambda k: nodes[k][0] - BW / 2, lambda k: nodes[k][0] + BW / 2
    T, B = lambda k: nodes[k][1] + BH / 2, lambda k: nodes[k][1] - BH / 2
    ny = lambda k: nodes[k][1]
    arr = dict(arrowstyle="-|>", lw=0.8, color=INK, mutation_scale=7, shrinkA=0, shrinkB=0)

    def promote(pts, color=INK, ls="solid"):
        ax.plot([p[0] for p in pts[:-1]], [p[1] for p in pts[:-1]], color=color, lw=0.8, ls=ls)
        ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arr, color=color, ls=ls))

    def inhibit(pts):
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=INK, lw=0.8)
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        dx, dy = x1 - x0, y1 - y0
        n = np.hypot(dx, dy); px, py = -dy / n * 0.022, dx / n * 0.022
        ax.plot([x1 - px, x1 + px], [y1 - py * 1.0, y1 + py * 1.0], color=INK, lw=1.3)

    def lab(x, y, s, **kw):
        ax.text(x, y, s, fontsize=6.0, color="#333333", **kw)

    # epidermal transport loop
    promote([(Rt("src"), ny("src")), (L("A"), ny("A"))]); lab((Rt("src") + L("A")) / 2, ny("A") + 0.012, "inward*", ha="center", va="bottom")
    promote([(Rt("A"), ny("A") + 0.03), (L("pin"), ny("pin") + 0.03)]); lab((Rt("A") + L("pin")) / 2, ny("A") + 0.042, "polarizes", ha="center", va="bottom")
    promote([(L("pin"), ny("pin") - 0.03), (Rt("A"), ny("A") - 0.03)]); lab((Rt("A") + L("pin")) / 2, ny("A") - 0.042, "transport", ha="center", va="top")
    # main chain
    promote([(XM, B("A")), (XM, T("M"))])
    promote([(XM, B("M")), (XM, T("ini"))])
    promote([(XM, B("ini")), (XM, T("pri"))]); lab(XM + 0.015, 0.388, "places", ha="left", va="center")
    promote([(XM, B("pri")), (XM, T("inner"))]); lab(XM + 0.015, 0.203, "drains", ha="left", va="center")
    promote([(L("M"), ny("M")), (Rt("dr5"), ny("dr5"))], color=GREY, ls=(0, (1.5, 1.5)))
    # primordium feedback
    inhibit([(Rt("pri"), ny("pri") - 0.03), (0.99, ny("pri") - 0.03), (0.99, 0.975), (XM, 0.975), (XM, T("A") + 0.014)])
    lab((XM + 0.99) / 2, 0.982, "sink", ha="center", va="bottom")
    promote([(Rt("pri"), ny("pri") + 0.03), (XR, ny("pri") + 0.03), (XR, B("pin"))])
    lab(XR + 0.012, 0.56, "polarity\ncue", ha="left", va="center", linespacing=1.0)
    promote([(L("pri"), ny("pri")), (XL, ny("pri")), (XL, B("inh"))]); lab(XL + 0.012, 0.375, "triggers", ha="left", va="center")
    inhibit([(Rt("inh"), ny("inh")), (L("ini") - 0.012, ny("ini"))]); lab((Rt("inh") + L("ini")) / 2, ny("ini") + 0.012, "raises θ", ha="center", va="bottom")


def fig2():
    z = np.load(HERE / "types.npz")
    m = np.load(HERE / "mech.npz")
    W, H = 6.3, 7.85
    fig = plt.figure(figsize=(W, H))
    box = lambda x, y, w, h: [x / W, y / H, w / W, h / H]

    # row 1: the model (A: 3D view of the two layers, B: loop that places primordia)
    T1, H1 = 4.95, 2.85
    a_img = os.environ.get("A_PANEL")                 # optional: panel A drawn in PowerPoint and rendered to PNG
    if a_img:
        ax = fig.add_axes(box(0.05, T1, 3.0, H1))
        ax.imshow(plt.imread(a_img), interpolation="lanczos"); ax.axis("off")
    else:
        ax = fig.add_axes(box(0.05, T1, 3.0, H1), projection="3d")
        mech_3d(ax, m)
    fig.text(0.08 / W, (T1 + H1) / H, "A", va="top", ha="left", **LETTER)
    ax = fig.add_axes(box(3.08, T1, 3.17, H1 - 0.05))
    b_img = os.environ.get("B_PANEL")                 # optional: panel B drawn in PowerPoint and rendered to PNG
    if b_img:
        ax.imshow(plt.imread(b_img), interpolation="lanczos"); ax.axis("off")
    else:
        loop_panel(ax)
    fig.text(3.08 / W, (T1 + H1) / H, "B", va="top", ha="left", **LETTER)

    # row 2: three patterns from the same equations
    S2, Y2 = 1.82, 2.62
    gap = (6.22 - 0.08 - 3 * S2) / 2
    for c, (name, en, rc) in enumerate(TYPES):
        x0 = 0.08 + c * (S2 + gap)
        ax = fig.add_axes(box(x0, Y2, S2, S2))
        pc = model_map(ax, z, name)
        par = json.loads(str(z[f"{name}_par"]))
        st = analysis.summarize([tuple(r) for r in z[f"{name}_log"]], par["gamma"])
        sub = (f"pairs, {st['rot_frac'] * 180:.0f}° between nodes" if st["jugacy"] >= 2
               else f"dominant angle {st['alpha']:.0f}°")
        ax.set_title(f"{en} ($R_\\mathrm{{c}}$ = {rc:g})\n{sub}", pad=2, fontsize=8)
        fig.text(x0 / W, (Y2 + S2) / H, "CDE"[c], va="top", ha="left", **LETTER)
    low_high_bar(fig, pc, box(W / 2 - 0.7, Y2 - 0.16, 1.4, 0.05), "Auxin (model)")

    # row 3: divergence angle against ring size, and temporal integration
    Y3, H3 = 0.45, 1.45
    ax = fig.add_axes(box(0.55, Y3, 2.5, H3))
    res = [json.loads(l) for l in open(MM / "out" / "e11_grid.jsonl", encoding="utf-8")]
    for r in res:
        if r["pattern"] == "none" or "alpha" not in r:
            continue
        o = r["over"]; kind = r["pattern"].rstrip("~"); reg = not r["pattern"].endswith("~")
        col = TYPE_COL.get(kind, GREY)
        yv = r["rot_frac"] * 180.0 if r.get("jugacy", 1) >= 2 else r["alpha"]     # pairs: rotation between nodes
        ax.scatter((o["R_c"] + 1.0) / o["w"], yv, s=11 if reg else 7, color=col if reg else "none",
                   ec=col if reg else LIGHT, lw=0.4, marker="D" if kind == "decussate" else "o", zorder=3 if reg else 2)
    for a, lab in ((180, "180°"), (137.5, "137.5°"), (90, "90°")):
        ax.axhline(a, color=GREY, ls=(0, (3, 2)), lw=0.6, zorder=1)
        ax.text(5.08, a, lab, fontsize=6.5, color="#555555", va="center")
    ax.set_xlim(0.8, 5.0); ax.set_ylim(0, 192)
    ax.set_xlabel("Ring mid-radius / primordium range"); ax.set_ylabel("Divergence angle (°)")
    hs = [plt.Line2D([], [], marker=mk, ls="", ms=4, color=TYPE_COL[k], label=l)
          for k, l, mk in (("distichous", "Distichous", "o"), ("spiral", "Spiral", "o"), ("decussate", "Decussate", "D"))]
    hs.append(plt.Line2D([], [], marker="o", ls="", ms=3.5, mfc="none", mec=GREY, label="Irregular"))
    ax.legend(handles=hs, frameon=False, loc="lower left", ncol=2, handletextpad=0.2, columnspacing=0.8, borderaxespad=0.2)
    fig.text(0.08 / W, (Y3 + H3 + 0.25) / H, "F", va="top", ha="left", **LETTER)

    ax = fig.add_axes(box(3.92, Y3, 2.3, H3))
    res = [json.loads(l) for l in open(MM / "out" / "e11_tau.jsonl", encoding="utf-8")]
    grp = defaultdict(list)
    for r in res:
        grp[("hot" if r["name"].startswith("hot") else "sub", r["over"]["tau_M"])].append(r)
    for key, lab, col, mk in (("sub", "Subcritical", GREEN, "o"), ("hot", "Supercritical", ORANGE, "s")):
        taus = sorted(t for (k, t) in grp if k == key)
        tp0 = np.mean([r["Tp"] for r in grp[(key, 0.0)] if r.get("Tp")])
        ys = [np.mean([(not r["pattern"].endswith("~")) and r["pattern"] != "none" for r in grp[(key, t)]]) for t in taus]
        ax.plot([t / tp0 for t in taus], ys, "-", color=col, lw=1.0, marker=mk, ms=3.8,
                label=f"{lab} (n = {len(grp[(key, 0.0)])})")
    ax.set_xlabel("Integration time constant / plastochron"); ax.set_ylabel("Fraction of regular spirals")
    ax.set_ylim(-0.04, 1.06); ax.set_xlim(-0.05, 1.42)
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.0, 1.0), handletextpad=0.4, borderaxespad=0.1)
    fig.text(3.45 / W, (Y3 + H3 + 0.25) / H, "G", va="top", ha="left", **LETTER)

    ppt = "".join(k for k in "AB" if os.environ.get(f"{k}_PANEL"))
    save(fig, "fig2_model" + (f"_ppt{ppt}" if ppt else ""), tight=False)


# ---------------------------------------------------------------- Fig. 3: tests against data (sampled model)
def fig3():
    D = MM / "detuned_v3" / "out"
    samples = json.load(open(D / "samples.json"))
    cal = {int(k): v for k, v in json.load(open(D / "calib.json")).items()}
    res = json.load(open(D / "runs.json"))
    runs = [r for r in res if r["T"] is None]
    r0 = {i: cal[i]["ratio_T0"] < samples[i]["theta_rel"] for i in cal}     # as in dv3_report.py
    nreg = defaultdict(int)
    for r in runs:
        if r.get("pattern") == "spiral":
            nreg[r["i"]] += 1

    fig = plt.figure(figsize=(6.3, 3.5))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.05], wspace=0.3)

    ax = fig.add_subplot(gs[0])
    for i, s in enumerate(samples):
        x, y = s["w"], s["kappa_c"]
        if not r0[i]:
            ax.scatter(x, y, marker="x", s=10, color=LIGHT, lw=0.7, zorder=1)
        elif nreg[i] == 0:
            ax.scatter(x, y, s=12, facecolor="white", ec=GREY, lw=0.6, zorder=2)
        else:
            ax.scatter(x, y, s=16 if nreg[i] == 1 else 26, color=INK, lw=0, zorder=3)
    hs = [plt.Line2D([], [], marker="o", ls="", ms=4.5, color=INK, label="Regular spiral"),
          plt.Line2D([], [], marker="o", ls="", ms=3.5, mfc="white", mec=GREY, label="Irregular"),
          plt.Line2D([], [], marker="x", ls="", ms=3.5, color=LIGHT, mew=0.8, label="Initiates without transport")]
    ax.legend(handles=hs, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=2, handletextpad=0.2,
              columnspacing=0.6, fontsize=6.5)
    ax.set_xlabel("Primordium range $w$ (cells)"); ax.set_ylabel("Centripetal transport bias $\\kappa_\\mathrm{c}$")
    ax.set_xlim(1.45, 3.05); ax.set_ylim(0.72, 1.53)
    panel_letter(ax, "A", dx=-0.16, dy=1.12)

    # B: model statistics vs measurements
    analysed = [r for r in runs if "alpha" in r]
    reg = [r for r in analysed if r["pattern"] == "spiral"]
    stats = [("alpha", "Mean divergence (°)", 1, (137.5, None), (80, 185)),
             ("spread", "P1–P5 spread (°)", 1, (6.7, None), (0, 120)),
             ("hours", "Plastochron (h)", 1, (12, (10, 14)), (0, 30)),
             ("co50", "Co-initiation (%)", 100, (28, None), (0, 80))]
    sub = gs[1].subgridspec(2, 2, wspace=0.5, hspace=0.62)
    rng = np.random.default_rng(1)
    for k, (key, lab, scale, (meas, band), ylim) in enumerate(stats):
        ax = fig.add_subplot(sub[k // 2, k % 2])
        for xpos, grp, col in ((0, analysed, GREY), (1, reg, INK)):
            v = np.array([r[key] for r in grp if r.get(key) is not None]) * scale
            v = v[np.isfinite(v)]
            ax.scatter(xpos + rng.uniform(-0.17, 0.17, len(v)), np.clip(v, *ylim), s=2.5, color=col, alpha=0.45, lw=0)
            ax.plot([xpos - 0.3, xpos + 0.3], [np.median(v)] * 2, color=col if xpos else "#555555", lw=1.4)
        if band:
            ax.axhspan(*band, color="#F2C6C2", lw=0, zorder=0)
        ax.axhline(meas, color=RED, lw=0.9, zorder=1)
        ax.set_xticks([0, 1]); ax.set_xticklabels([tr("All runs"), tr("Regular\nspirals")], fontsize=6.5)
        ax.set_xlim(-0.55, 1.55); ax.set_ylim(*ylim)
        ax.set_title(lab, fontsize=7.5, pad=3)
        if k == 0:
            panel_letter(ax, "B", dx=-0.3, dy=1.12)

    save(fig, "fig3_tests")
    print("regular-spiral runs", len(reg), "of", len(runs), "| R0 samples", sum(r0.values()))


def save(fig, stem, tight=True):
    localize(fig)
    stem = stem + SUFFIX
    for ext in ("png", "pdf"):
        if tight:
            fig.savefig(HERE / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.03)
        else:
            fig.savefig(HERE / f"{stem}.{ext}")
    plt.close(fig)
    print("wrote", stem)


if __name__ == "__main__":
    fig1(); fig2(); fig3()
