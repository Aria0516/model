"""Error-reduction figure (candidates 1, 3, 5) and a side-by-side with the measured meristem.

python figs7.py fig | gif | data
"""
import csv
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi

import figs  # noqa: F401  (fonts)
import viz
from e10_phase_sub import OP
from model import Sim
from nexp import ARABIDOPSIS_LIKE, FIELD


def angles(job):
    name, over, seed = job
    p = dict(OP, w=2.0, R_c=5.5, R_p=7.5, R_out=14.5, t_end=600.0, mesh_seed=seed, seed=seed, **over)
    sim = Sim(p).run()
    th = np.degrees(np.arctan2([l[2] for l in sim.log], [l[1] for l in sim.log])) % 360
    d = (np.diff(th) % 360)[len(th) // 3:]
    if (d < 180).mean() < 0.5:
        d = 360 - d                                    # express every run in its own dominant handedness
    return name, d.tolist()


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def clean(rs):
    return [r for r in rs if r.get("jugacy", 9) <= 1 and r.get("f_perm", 1) == 0 and r.get("f_other", 1) <= 0.03]


def fig():
    cases = {"无次级场，瞬时定位": {}, "加次级场，瞬时定位": dict(FIELD), "加次级场，跟随后定位": dict(FIELD, commit="track", tau_c=2.0)}
    with Pool(28) as pool:
        res = pool.map(angles, [(n, o, s) for n, o in cases.items() for s in range(1, 17)])
    fig, axs = plt.subplots(1, 3, figsize=(17, 5.0), gridspec_kw=dict(width_ratios=[1.15, 0.9, 1.2]))
    ax = axs[0]
    bins = np.arange(0, 361, 7.5)
    for (name, col) in zip(cases, ("#999999", "#D55E00", "#009E73")):
        d = np.concatenate([np.array(r[1]) for r in res if r[0] == name])
        ax.hist(d, bins=bins, histtype="step", lw=1.8, color=col, density=True,
                label=f"{name}（{len(d)} 个夹角，{100*np.mean(np.abs(d-np.median(d))<30):.0f}% 在中位数 ±30° 内）")
        print(name, "n", len(d), "median", round(float(np.median(d)), 1), "mean within 30", round(float(d[np.abs(d - np.median(d)) < 30].mean()), 2),
              "sd within 30", round(float(d[np.abs(d - np.median(d)) < 30].std()), 2))
    ax.axvline(137.5, color="k", ls="--", lw=0.8); ax.text(139, ax.get_ylim()[1] * 0.93, "137.5°", fontsize=9)
    for a, lab in ((275, "2α"), (222.5, "−α")):
        ax.axvline(a, color="k", ls=":", lw=0.6); ax.text(a + 2, ax.get_ylim()[1] * 0.6, lab, fontsize=8)
    ax.set_xlim(0, 360); ax.set_xlabel("相邻原基的夹角（度；各运行按自身手性表示）"); ax.set_ylabel("概率密度")
    ax.legend(frameon=False, fontsize=8, loc="center right", bbox_to_anchor=(1.0, 0.55)); ax.set_title("拟南芥径向比处的夹角分布（各 16 个种子）", fontsize=10)

    ax = axs[1]
    a1 = load("out/n09_a1.jsonl"); ranks = np.arange(1, 7)
    for name, col, lab in (("instant", "#D55E00", "瞬时定位"), ("track tau_c=2", "#009E73", "跟随后定位")):
        rs = clean([r for r in a1 if r["name"] == name])
        m = np.nanmean(np.array([r["rank"] for r in rs]), axis=0)
        ax.plot(ranks, m, "o-", color=col, label=f"{lab}（{len(rs)} 次无置换运行）")
    ax.axhline(6.7, color="k", ls="--", lw=0.8); ax.text(6.0, 6.9, "论文实测 P1–P5 平均 6.7°", ha="right", fontsize=8.5)
    ax.plot(ranks, 3.6 * np.sqrt(ranks), "k:", label="论文的随机游走模型")
    ax.set_ylim(0, 12); ax.set_xlabel("与较老原基的序号差"); ax.set_ylabel("相对夹角的离散（度）")
    ax.legend(frameon=False, fontsize=8.5, loc="lower right"); ax.set_title("角度精度（与论文同一口径）", fontsize=10)

    ax = axs[2]
    rows = []
    for path, point, picks in (("out/n06.jsonl", "lowG+field", [("instant (ref)", "参照"), ("patch n=5", "① 成片后定位"), ("track tau_c=2", "① 跟随后定位")]),
                               ("out/n07.jsonl", "lowG+field", [("grow 1.0 cap x2", "③ 汇范围随年龄增大"), ("fade after x1.6", "③ 汇与线索随年龄消退"),
                                                               ("sink fades x1.6, cue stays", "③ 仅汇消退")]),
                               ("out/n08.jsonl", "lowG", [("ref (no pool, no field)", "⑤ 参照（无次级场）"), ("mixed CZ", "⑤ 中央区混匀"),
                                                         ("CZ supplies (18/6), low PIN", "⑤ 中央区供给")])):
        res_ = load(path)
        for key, lab in picks:
            rs = [r for r in res_ if r["point"] == point and r["name"] == key and r["pattern"] not in ("ERROR", "none")]
            rows.append((lab, np.mean([not r["pattern"].endswith("~") for r in rs]), 100 * (1 - np.mean([r["f_alpha"] for r in rs]))))
    y = np.arange(len(rows))[::-1]
    ax.barh(y, [r[1] for r in rows], color=["#009E73" if "①" in r[0] or r[0] == "参照" else "#0072B2" if "③" in r[0] else "#CC79A7" for r in rows], height=0.62)
    for yy, r in zip(y, rows):
        ax.text(r[1] + 0.02, yy, f"非规范夹角 {r[2]:.0f}%", va="center", fontsize=8.5)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=9); ax.set_xlim(0, 1.45); ax.set_xticks([0, 0.5, 1.0])
    ax.set_xlabel("得到规则叶序的运行比例（10 个种子）"); ax.set_title("三项候选处理的效果（拟南芥径向比处）", fontsize=10)
    fig.tight_layout(); fig.savefig("out/fig_error_reduction.png", dpi=110); plt.close(fig); print("saved out/fig_error_reduction.png")


def gif():
    import imageio.v2 as imageio
    sim = Sim(dict(ARABIDOPSIS_LIKE, t_end=420.0, snap_dt=1.5)).run()
    snaps = [s for s in sim.snaps if s["t"] >= 300.0]
    vmax = np.percentile(np.concatenate([s["A"] for s in snaps]), 99.5)
    frames = []
    for s in snaps:
        f, ax = plt.subplots(figsize=(5.6, 5.6))
        viz.draw_tissue(ax, s["pts"], s["A"], s["prim"], sim.p, 0, vmax, pin=s["pin"])
        ax.set_title(f"t = {s['t']:.0f}   白箭头: PIN1 平均方向   编号: 原基产生顺序", fontsize=9)
        f.tight_layout(); f.canvas.draw()
        frames.append(np.asarray(f.canvas.buffer_rgba())[:, :, :3].copy()); plt.close(f)
    imageio.mimsave("out/arabidopsis_like.gif", frames, duration=0.12, loop=0)
    print("saved out/arabidopsis_like.gif", len(frames), "frames")


def data():
    base = Path(__file__).resolve().parents[1] / "reproductions" / "elife55832" / "outputs" / "historic_nuclei_images" / \
        "qDII-DR5-CLV3-LD_E27_170817_sam07" / "qDII-DR5-CLV3-LD_E27_170817_sam07_t00"
    stem = "qDII-DR5-CLV3-LD_E27_170817_sam07_t00_"
    rd = lambda n: list(csv.DictReader(open(base / (stem + n), newline="", encoding="utf-8")))
    cells = rd("aligned_L1_normalized_signal_data.csv")
    x = np.array([float(c["aligned_x"]) for c in cells]); y = np.array([float(c["aligned_y"]) for c in cells])
    aux = np.array([float(c["Auxin"]) for c in cells]); rclv = float(cells[0]["clv3_radius"])
    ext = [e for e in rd("aligned_primordia_extrema.csv") if e["extremum_type"] == "minimum"]
    fig, axs = plt.subplots(1, 2, figsize=(13, 6.2))
    ax = axs[0]
    ang = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    vor = Voronoi(np.vstack([np.c_[x, y], (np.hypot(x, y).max() + 8) * np.c_[np.cos(ang), np.sin(ang)]]))
    pc = PolyCollection([vor.vertices[vor.regions[vor.point_region[k]]] for k in range(len(x))], array=aux, cmap="viridis",
                        edgecolors="k", linewidths=0.15)
    ax.add_collection(pc); plt.colorbar(pc, ax=ax, fraction=0.046, pad=0.02, label="生长素代理 1 − qDII")
    ax.add_patch(plt.Circle((0, 0), rclv, fill=False, color="r", ls="--", lw=1.0))
    for e in ext:
        ax.text(float(e["aligned_x"]), float(e["aligned_y"]), "P" + e["primordium"], color="w", fontsize=8, ha="center", va="center", weight="bold")
    ax.set_title(f"实测：E27/SAM7，0 h，L1 层 {len(x)} 个细胞\n红圈为 CLV3 半径 {rclv:.0f} µm；标注为自动检测的最大区阶段", fontsize=10)
    um = 6.0
    sim = Sim(dict(ARABIDOPSIS_LIKE, t_end=400.0, snap_dt=399.0)).run()
    sn = sim.snaps[-1]
    ax = axs[1]
    pc = PolyCollection([um * q for q in viz.polygons(sn["pts"], sim.p["R_out"])], array=sn["A"], cmap="viridis", edgecolors="k", linewidths=0.15)
    ax.add_collection(pc); plt.colorbar(pc, ax=ax, fraction=0.046, pad=0.02, label="模型生长素浓度")
    for rr in (sim.p["R_c"], sim.p["R_p"]):
        ax.add_patch(plt.Circle((0, 0), um * rr, fill=False, color="r", ls="--", lw=1.0))
    newest = max(q[2] for q in sn["prim"])
    for (px, py, pid, age) in sn["prim"]:
        ax.text(um * px, um * py, f"P{newest - pid}", color="w", fontsize=8, ha="center", va="center", weight="bold")
    ax.set_title(f"模型：拟南芥径向比工作点的一帧（1 个长度单位按 {um:g} µm 换算）\n红圈为发生环内外边界；标注为原基的先后（P0 最新）", fontsize=10)
    for a in axs:
        a.set_xlim(-88, 88); a.set_ylim(-88, 88); a.set_aspect("equal"); a.set_xlabel("µm")
    fig.suptitle("同一比例下的静态对照：实测中央区为高生长素、起始半径约 30 µm；模型中央区偏低、起始半径约 40 µm", fontsize=12)
    fig.tight_layout(); fig.savefig("out/fig_data_vs_model.png", dpi=110); plt.close(fig); print("saved out/fig_data_vs_model.png")


if __name__ == "__main__":
    {"fig": fig, "gif": gif, "data": data}[sys.argv[1]]()
