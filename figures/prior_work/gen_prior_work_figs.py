#!/usr/bin/env python3
"""Figures for the "已有工作积累" section of the thesis proposal.

    python run_types.py            # once: three model runs for Fig. 2A-C (types.npz)
    python gen_prior_work_figs.py  # fig1_data.png, fig2_model.png, fig3_tests.png (+ .pdf)

Every number drawn here is read from files already in the repository:
  Fig. 1  reproductions/elife55832/outputs/nuclei_21/   (pipeline output, 21 meristems)
          model_mvp/calib_v2/out/measure_nuclei_21.json (cell spacing, CLV3 radius, P0 radius)
          model_mvp/noise_v3/out/pin1_measure.json       (cell-to-cell PIN1 spread, 4 meristems)
          model_mvp/noise_v3/RESULTS.md                  (sigma needed by the model: 0.32 / 0.48)
  Fig. 2  types.npz (run_types.py), model_mvp/out/e11_grid.jsonl, model_mvp/out/e11_tau.jsonl
  Fig. 3  model_mvp/detuned_v3/out/{samples,calib,runs}.json (classification as in dv3_report.py)
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MM = ROOT / "model_mvp"
NUC = ROOT / "reproductions" / "elife55832" / "outputs" / "nuclei_21"
sys.path.insert(0, str(MM))
import analysis  # noqa: E402  (model_mvp/analysis.py: pattern statistics)

# Song-style CJK + Times-style Latin, as in the proposal's own figure
plt.rcParams.update({
    "font.family": ["Times New Roman", "Liberation Serif", "SimSun", "Noto Serif CJK SC"],
    "mathtext.fontset": "custom", "mathtext.rm": "Noto Serif CJK SC", "mathtext.it": "Liberation Serif:italic", "mathtext.bf": "Noto Serif CJK SC:bold", "mathtext.fallback": "stix", "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "axes.unicode_minus": False, "savefig.dpi": 300,
})
INK, GREY, LIGHT = "#1A1A1A", "#8C8C8C", "#D0D0D0"
BLUE, GREEN, ORANGE, RED = "#0072B2", "#009E73", "#D55E00", "#C0392B"
TYPE_COL = {"distichous": BLUE, "intermediate": "#56B4E9", "spiral": GREEN, "decussate": ORANGE}
OUTLINE = [pe.withStroke(linewidth=1.2, foreground="black")]


def panel_letter(ax, s, dx=-0.02, dy=1.02):
    ax.text(dx, dy, s, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom", ha="right",
            family=["Liberation Sans", "DejaVu Sans"])


def voronoi_cells(x, y, rmax):
    """Voronoi polygons of the points, clipped to a disc of radius rmax (ghost ring outside)."""
    k = np.arange(96) * 2 * np.pi / 96
    ghost = np.c_[1.25 * rmax * np.cos(k), 1.25 * rmax * np.sin(k)]
    vor = Voronoi(np.vstack([np.c_[x, y], ghost]))
    polys = []
    for i in range(len(x)):
        reg = vor.regions[vor.point_region[i]]
        poly = vor.vertices[reg]
        r = np.hypot(poly[:, 0], poly[:, 1])
        poly = poly * np.minimum(1.0, rmax / np.maximum(r, 1e-9))[:, None]
        polys.append(poly)
    return polys


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
    ax.add_patch(plt.Circle((0, 0), sig["clv3_r"], fill=False, ec="white", ls=(0, (4, 2)), lw=0.9))
    for k in show:
        if k in prim:
            px, py = prim[k]
            ax.plot(px, py, "o", ms=9, mfc="none", mec="white", mew=0.9)
            lab = "P0" if k == 0 else (f"P{k}" if k > 0 else f"P−{-k}")
            ax.text(px, py + 7.5, lab, color="white", ha="center", va="bottom", fontsize=7.5, fontweight="bold",
                    path_effects=OUTLINE)
    ax.plot([-RMAX + 2, -RMAX + 22], [-RMAX + 1, -RMAX + 1], color="white", lw=1.6, solid_capstyle="butt",
            path_effects=[pe.withStroke(linewidth=2.6, foreground="black")])
    ax.text(-RMAX + 12, -RMAX + 4, "20 µm", color="white", ha="center", va="bottom", fontsize=6.5, path_effects=OUTLINE)
    ax.set_xlim(-RMAX - 1, RMAX + 1); ax.set_ylim(-RMAX - 1, RMAX + 1); ax.set_aspect("equal"); ax.axis("off")
    cax = ax.inset_axes([0.18, -0.07, 0.64, 0.035])
    cb = plt.colorbar(pc, cax=cax, orientation="horizontal")
    cb.set_ticks([lo, hi]); cb.set_ticklabels(["低", "高"]); cb.outline.set_linewidth(0.4)
    cax.tick_params(length=0, pad=1.5, labelsize=6.5)


def fig1():
    meas = json.load(open(MM / "calib_v2" / "out" / "measure_nuclei_21.json"))
    pin = json.load(open(MM / "noise_v3" / "out" / "pin1_measure.json"))
    sig, prim = load_sam(EXAMPLE)

    fig = plt.figure(figsize=(6.3, 5.15))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.32, 1.0], hspace=0.42)
    top = gs[0].subgridspec(1, 2, wspace=0.08)
    bot = gs[1].subgridspec(1, 3, wspace=0.55, width_ratios=[0.75, 1.25, 0.95])

    ax = fig.add_subplot(top[0]); sam_map(ax, sig, prim, "auxin", "viridis")
    ax.set_title("生长素输入（1 − qDII）", pad=3); panel_letter(ax, "A", dx=0.04, dy=0.98)
    ax = fig.add_subplot(top[1]); sam_map(ax, sig, prim, "dr5", "magma")
    ax.set_title("DR5 转录输出", pad=3); panel_letter(ax, "B", dx=0.04, dy=0.98)

    rng = np.random.default_rng(0)
    d = np.array([m["d"] for m in meas])
    clv = np.array([m["clv3_radius"] for m in meas])
    p0 = np.array([m["p0_radius_t00"] for m in meas if m.get("p0_radius_t00") is not None])

    def strip(ax, xpos, vals, col):
        ax.scatter(xpos + rng.uniform(-0.13, 0.13, len(vals)), vals, s=9, color=col, alpha=0.85, lw=0, zorder=3)
        q1, med, q3 = np.percentile(vals, [25, 50, 75])
        ax.plot([xpos - 0.26, xpos + 0.26], [med, med], color=INK, lw=1.2, zorder=4)
        ax.plot([xpos, xpos], [q1, q3], color=INK, lw=0.8, zorder=4)

    ax = fig.add_subplot(bot[0])
    strip(ax, 0, d, GREY)
    ax.set_xticks([0]); ax.set_xticklabels(["L1 细胞核\n最近邻间距"]); ax.set_xlim(-0.6, 0.6)
    ax.set_ylabel("µm"); ax.set_ylim(4.2, 4.85)
    ax.text(0.33, np.median(d), f"{np.median(d):.2f}", va="center", fontsize=7)
    ax.set_title(f"{len(d)} 个茎尖", pad=3); panel_letter(ax, "C", dx=-0.42)

    ax = fig.add_subplot(bot[1])
    strip(ax, 0, clv, GREEN); strip(ax, 1, p0, ORANGE)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["CLV3 区半径", "P0 距中心（0 h）"]); ax.set_xlim(-0.6, 1.6)
    ax.set_ylabel("µm"); ax.set_ylim(10, 45)
    for xpos, vals in ((0, clv), (1, p0)):
        ax.text(xpos + 0.33, np.median(vals), f"{np.median(vals):.1f}", va="center", fontsize=7)
    ax.set_title(f"{len(clv)} 个茎尖（P0：{len(p0)} 个）", pad=3); panel_letter(ax, "D", dx=-0.2)

    ax = fig.add_subplot(bot[2])
    sp = np.array([p["sigma_PIN"] for p in pin])
    ax.axhspan(0.32, 0.48, color=LIGHT, lw=0, zorder=0)
    ax.text(0.5, 0.40, "模型再现实测\n不规则性所需", ha="center", va="center", fontsize=6.5, color="#444444",
            transform=ax.get_yaxis_transform())
    ax.scatter(rng.uniform(-0.12, 0.12, len(sp)) + 0.5, sp, s=14, color=BLUE, zorder=3, lw=0)
    ax.plot([0.25, 0.75], [np.median(sp)] * 2, color=INK, lw=1.2)
    ax.text(0.8, np.median(sp), f"{np.median(sp):.2f}", va="center", fontsize=7)
    ax.set_xlim(0, 1); ax.set_xticks([0.5]); ax.set_xticklabels(["实测（4 个茎尖）"])
    ax.set_ylim(0, 0.55); ax.set_ylabel("细胞间 PIN1 差异（对数标准差）")
    ax.set_title("PIN1 量的细胞间差异", pad=3); panel_letter(ax, "E", dx=-0.42)

    save(fig, "fig1_data")


# ---------------------------------------------------------------- Fig. 2: model
TYPES = [("distichous", "二列互生", 2.5), ("spiral", "螺旋", 3.5), ("decussate", "交互对生", 6.0)]


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


def divergence(log):
    th = np.degrees(np.arctan2(log[:, 2], log[:, 1])) % 360
    d = np.diff(th) % 360
    return np.minimum(d, 360 - d)


def fig2():
    z = np.load(HERE / "types.npz")
    fig = plt.figure(figsize=(6.3, 5.0))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.95], hspace=0.38)
    top = gs[0].subgridspec(1, 3, wspace=0.06)
    bot = gs[1].subgridspec(1, 2, wspace=0.32)

    for c, (name, zh, rc) in enumerate(TYPES):
        ax = fig.add_subplot(top[c])
        pc = model_map(ax, z, name)
        par = json.loads(str(z[f"{name}_par"]))
        st = analysis.summarize([tuple(r) for r in z[f"{name}_log"]], par["gamma"])
        if st["jugacy"] >= 2:
            sub = f"每节 2 个原基，相邻两节转 {st['rot_frac'] * 180:.0f}°"
        else:
            sub = f"主导夹角 {st['alpha']:.0f}°"
        print(name, analysis.fmt(st))
        ax.set_title(f"{zh}（$R_\\mathrm{{c}}$ = {rc:g}）\n{sub}", pad=2, fontsize=7.5, family="Noto Serif CJK SC")
        panel_letter(ax, "ABC"[c], dx=0.06, dy=0.90)
    cax = fig.add_axes([0.40, 0.535, 0.22, 0.01])
    cb = plt.colorbar(pc, cax=cax, orientation="horizontal")
    cb.set_ticks(pc.get_clim()); cb.set_ticklabels(["低", "高"]); cb.outline.set_linewidth(0.4)
    cax.tick_params(length=0, pad=1.5, labelsize=6.5)
    cax.set_xlabel("模型生长素浓度", fontsize=7, labelpad=1)

    # D: dominant divergence angle against ring radius / sink range (e11_grid)
    ax = fig.add_subplot(bot[0])
    res = [json.loads(l) for l in open(MM / "out" / "e11_grid.jsonl", encoding="utf-8")]
    for r in res:
        if r["pattern"] == "none" or "alpha" not in r:
            continue
        o = r["over"]; kind = r["pattern"].rstrip("~"); reg = not r["pattern"].endswith("~")
        x = (o["R_c"] + 1.0) / o["w"]
        col = TYPE_COL.get(kind, GREY)
        yv = r["rot_frac"] * 180.0 if r.get("jugacy", 1) >= 2 else r["alpha"]     # pairs: rotation between nodes
        ax.scatter(x, yv, s=11 if reg else 7, color=col if reg else "none", ec=col if reg else LIGHT,
                   lw=0.4, alpha=0.95 if reg else 0.9, marker="D" if kind == "decussate" else "o", zorder=3 if reg else 2)
    for a, lab in ((180, "180°"), (137.5, "137.5°"), (90, "90°")):
        ax.axhline(a, color=GREY, ls=(0, (3, 2)), lw=0.6, zorder=1)
        ax.text(5.08, a, lab, fontsize=6.5, color="#555555", va="center")
    ax.set_xlim(0.8, 5.0); ax.set_ylim(0, 192)
    ax.set_xlabel("发生环中线半径 / 原基作用范围"); ax.set_ylabel("相邻原基夹角（°）")
    hs = [plt.Line2D([], [], marker=m, ls="", ms=4, color=TYPE_COL[k], label=l)
          for k, l, m in (("distichous", "二列互生", "o"), ("spiral", "螺旋", "o"), ("decussate", "交互对生", "D"))]
    hs.append(plt.Line2D([], [], marker="o", ls="", ms=3.5, mfc="none", mec=GREY, label="不规则"))
    ax.legend(handles=hs, frameon=False, loc="lower left", ncol=2, handletextpad=0.2, columnspacing=0.8, borderaxespad=0.2)
    panel_letter(ax, "D", dx=-0.13)

    # E: leaky temporal integration in the loop (e11_tau)
    ax = fig.add_subplot(bot[1])
    res = [json.loads(l) for l in open(MM / "out" / "e11_tau.jsonl", encoding="utf-8")]
    grp = defaultdict(list)
    for r in res:
        key = "hot" if r["name"].startswith("hot") else "sub"
        grp[(key, r["over"]["tau_M"])].append(r)
    for key, lab, col, mk in (("sub", "不自发成峰", GREEN, "o"), ("hot", "自发成峰", ORANGE, "s")):
        taus = sorted(t for (k, t) in grp if k == key)
        tp0 = np.mean([r["Tp"] for r in grp[(key, 0.0)] if r.get("Tp")])
        xs = [t / tp0 for t in taus]
        ys = [np.mean([(not r["pattern"].endswith("~")) and r["pattern"] != "none" for r in grp[(key, t)]]) for t in taus]
        ns = [len(grp[(key, t)]) for t in taus]
        ax.plot(xs, ys, "-", color=col, lw=1.0, marker=mk, ms=3.8, label=f"{lab}（每点 {ns[0]} 次）")
    ax.set_xlabel("积分时间常数 / 叶间期"); ax.set_ylabel("规则螺旋所占比例")
    ax.set_ylim(-0.04, 1.06); ax.set_xlim(-0.05, 1.42)
    ax.legend(frameon=False, loc="upper right", bbox_to_anchor=(1.0, 0.9), handletextpad=0.4, borderaxespad=0.1)
    panel_letter(ax, "E", dx=-0.13)

    save(fig, "fig2_model")


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
    hs = [plt.Line2D([], [], marker="o", ls="", ms=4.5, color=INK, label="出现规则螺旋"),
          plt.Line2D([], [], marker="o", ls="", ms=3.5, mfc="white", mec=GREY, label="不规则"),
          plt.Line2D([], [], marker="x", ls="", ms=3.5, color=LIGHT, mew=0.8, label="无运输也能起始")]
    ax.legend(handles=hs, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=2, handletextpad=0.2,
              columnspacing=0.6, fontsize=6.5)
    ax.set_xlabel("原基作用范围 $w$（细胞）", family="Noto Serif CJK SC"); ax.set_ylabel("向心运输偏置 $κ_\\mathrm{c}$", family="Noto Serif CJK SC")
    ax.set_xlim(1.45, 3.05); ax.set_ylim(0.72, 1.53)
    panel_letter(ax, "A", dx=-0.16, dy=1.12)

    # B: model statistics vs measurements
    analysed = [r for r in runs if "alpha" in r]
    reg = [r for r in analysed if r["pattern"] == "spiral"]
    stats = [("alpha", "平均发散角（°）", 1, (137.5, None), (80, 185)),
             ("spread", "P1–P5 夹角离散（°）", 1, (6.7, None), (0, 120)),
             ("hours", "原基间隔（h）", 1, (12, (10, 14)), (0, 30)),
             ("co50", "同时起始比例（%）", 100, (28, None), (0, 80))]
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
        ax.set_xticks([0, 1]); ax.set_xticklabels(["全部运行", "规则螺旋"], fontsize=6.5)
        ax.set_xlim(-0.55, 1.55); ax.set_ylim(*ylim)
        ax.set_title(lab, fontsize=7, pad=3)
        if k == 0:
            panel_letter(ax, "B", dx=-0.3, dy=1.12)

    save(fig, "fig3_tests")
    print("regular-spiral runs", len(reg), "of", len(runs), "| R0 samples", sum(r0.values()))


def save(fig, stem):
    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("wrote", stem)


if __name__ == "__main__":
    fig1(); fig2(); fig3()
