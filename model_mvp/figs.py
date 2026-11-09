"""Figures for the v1 model: python figs.py types | phase | tau | regime | modules | gif"""
import json
import math
import sys
from collections import Counter, defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import analysis
import viz
from e10_phase_sub import OP
from model import Sim

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"], "axes.unicode_minus": False})
COL = {"distichous": "#0072B2", "intermediate": "#56B4E9", "spiral": "#009E73", "lucas": "#CC79A7",
       "decussate": "#D55E00", "tricussate": "#E69F00", "other": "#999999", "multijugate2": "#999999", "none": "#DDDDDD"}
ZH = {"distichous": "二列互生", "intermediate": "过渡角", "spiral": "螺旋", "decussate": "交互对生",
      "tricussate": "三轮生", "lucas": "Lucas 螺旋", "other": "不规则", "multijugate2": "不规则", "none": "无原基"}


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def floral(ax, log, gamma, t_end, n_last=18):
    """Top-view diagram of the last organs, radius linear in age (classic phyllotaxis diagram)."""
    t = np.array([l[0] for l in log]); th = np.arctan2([l[2] for l in log], [l[1] for l in log])
    t, th = t[-n_last:], th[-n_last:]
    age = t_end - t
    r = 1.0 + age / max(age.max(), 1e-9) * 3.0
    order = np.arange(len(t))
    ax.scatter(r * np.cos(th), r * np.sin(th), s=160, c=order, cmap="YlGn", edgecolors="k", linewidths=0.6, zorder=3)
    for k in range(len(t)):
        ax.text(r[k] * math.cos(th[k]), r[k] * math.sin(th[k]), str(len(t) - k), ha="center", va="center", fontsize=7, zorder=4)
    for rr in (2.0, 3.0, 4.0):
        ax.add_patch(plt.Circle((0, 0), rr, fill=False, color="#CCCCCC", lw=0.5, zorder=0))
    ax.add_patch(plt.Circle((0, 0), 0.8, fill=False, color="r", ls="--", lw=0.8))
    ax.set_xlim(-4.6, 4.6); ax.set_ylim(-4.6, 4.6); ax.set_aspect("equal"); ax.axis("off")


def fig_types(out="out/fig_types.png"):
    cases = [("二列互生", 2.5, 1), ("螺旋", 3.5, 1), ("交互对生", 6.0, 1)]
    fig, axs = plt.subplots(3, 3, figsize=(13.5, 13))
    for c, (name, rc, seed) in enumerate(cases):
        sim = Sim(dict(OP, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0, t_end=800.0, mesh_seed=seed, seed=seed, snap_dt=799.0)).run()
        s = analysis.summarize(sim.log, sim.p["gamma"])
        sn = sim.snaps[-1]
        viz.draw_tissue(axs[0, c], sn["pts"], sn["A"], sn["prim"], sim.p, 0, None, pin=sn["pin"], label=False,
                        cbar="生长素浓度")
        axs[0, c].set_title(f"{name}：环内半径 {rc:g} 个细胞")
        floral(axs[1, c], sim.log, sim.p["gamma"], sim.p["t_end"])
        axs[1, c].set_title("最近 18 个原基的俯视排列（1 为最新）", fontsize=9)
        t = np.array([l[0] for l in sim.log]); th = np.degrees(np.arctan2([l[2] for l in sim.log], [l[1] for l in sim.log])) % 360
        d = np.diff(th) % 360
        ax = axs[2, c]
        ax.plot(np.arange(1, len(th)), np.minimum(d, 360 - d), "o-", ms=3.5, lw=0.8, color="k")
        for a, lab in ((137.5, "137.5°"), (180, "180°"), (90, "90°")):
            ax.axhline(a, color="r", ls="--", lw=0.7); ax.text(len(th), a + 2, lab, color="r", fontsize=8, ha="right")
        ax.set_ylim(0, 190); ax.set_xlabel("原基序号"); ax.set_ylabel("相邻原基夹角（度）")
        if s["jugacy"] <= 1:
            ttl = f"主导夹角 {s['alpha']:.1f}°，{s['f_alpha']*100:.0f}% 的夹角落在 ±30° 内；间隔变异系数 {s['gap_cv']:.2f}"
        else:
            ttl = f"每节 {s['jugacy']} 个原基（{s['frac_nodes_full']*100:.0f}% 的节完整）；相邻节转角 {s['rot_frac']*180:.0f}°"
        ax.set_title(ttl, fontsize=8.5)
        print(name, analysis.fmt(s))
    fig.suptitle("同一套方程，只改变中央区（发生环）大小：从噪声出发得到三种叶序", fontsize=13)
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig); print("saved", out)


def fig_phase(path="out/e11_grid.jsonl", out="out/fig_phase.png"):
    res = load(path)
    by = defaultdict(list)
    for r in res:
        o = r["over"]; by[(o["w"], o["R_c"])].append(r)
    ws = sorted({k[0] for k in by}); rcs = sorted({k[1] for k in by})
    fig, axs = plt.subplots(1, 2, figsize=(15, 5.6))
    ax = axs[0]
    for (w, rc), rs in by.items():
        pats = Counter(r["pattern"].rstrip("~") for r in rs)
        reg = np.mean([not r["pattern"].endswith("~") and r["pattern"] != "none" for r in rs])
        name = pats.most_common(1)[0][0]
        ax.scatter(rc, w, s=1500, marker="s", color=COL.get(name, "#999999"), alpha=0.25 + 0.75 * reg, edgecolors="none")
        a = np.median([r.get("alpha", np.nan) for r in rs])
        ax.text(rc, w, f"{a:.0f}°\n{int(round(reg * len(rs)))}/{len(rs)}", ha="center", va="center", fontsize=8)
    ax.set_xlabel("发生环内半径 R_c（细胞直径）"); ax.set_ylabel("原基汇的范围 w（细胞直径）")
    ax.set_xticks(rcs); ax.set_yticks(ws); ax.set_xlim(min(rcs) - 0.5, max(rcs) + 0.6); ax.set_ylim(min(ws) - 0.35, max(ws) + 0.35)
    hs = [plt.Line2D([], [], marker="s", ls="", ms=11, color=COL[k], label=ZH[k]) for k in ("distichous", "intermediate", "spiral", "decussate", "other")]
    ax.legend(handles=hs, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.13), frameon=False)
    ax.set_title("格内：主导发散角；规则运行数/总数（颜色越实越规则）", fontsize=9, y=-0.22)
    ax = axs[1]
    for r in res:
        if r["pattern"] == "none":
            continue
        o = r["over"]; name = r["pattern"].rstrip("~")
        x = (o["R_c"] + 1.0) / o["w"]
        ax.scatter(x, r["alpha"], s=28, color=COL.get(name, "#999999"), alpha=0.9 if not r["pattern"].endswith("~") else 0.3,
                   edgecolors="k" if not r["pattern"].endswith("~") else "none", linewidths=0.4)
    for a in (137.5, 180, 90):
        ax.axhline(a, color="r", ls="--", lw=0.7)
    ax.set_xlabel("环中线半径 / 汇范围  (R_c+1)/w"); ax.set_ylabel("主导夹角 α（度）")
    ax.set_title("实心描边 = 规则；浅色 = 不规则", fontsize=9)
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig); print("saved", out)


def fig_tau(path="out/e11_tau.jsonl", out="out/fig_tau.png"):
    res = load(path)
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.4))
    ALL = [0.0, 1.0, 2.0, 5.0, 10.0, 20.0]
    groups = {"亚临界，R_c=3.5": ("sub Rc3.5", "#009E73"), "亚临界，R_c=4.0": ("sub Rc4.0", "#0072B2"), "超临界（成核）": ("hot", "#D55E00")}
    for lab, (key, col) in groups.items():
        rs = [r for r in res if r["name"].startswith(key)]
        taus = sorted({r["over"]["tau_M"] for r in rs})
        f1, cv, ok = [], [], []
        for tau in taus:
            q = [r for r in rs if r["over"]["tau_M"] == tau]
            f1.append(np.mean([r.get("f_alpha", 0.0) for r in q]))
            cv.append(np.mean([r.get("gap_cv", np.nan) for r in q if r["pattern"] != "none"]) if any(r["pattern"] != "none" for r in q) else np.nan)
            ok.append(np.mean([(not r["pattern"].endswith("~")) and r["pattern"] != "none" for r in q]))
        xs = [ALL.index(t) for t in taus]
        axs[0].plot(xs, ok, "o-", color=col, label=lab)
        axs[1].plot(xs, cv, "o-", color=col, label=lab)
    for a in axs:
        a.set_xticks(range(len(ALL))); a.set_xticklabels([f"{t:g}" for t in ALL])
    axs[0].set_ylabel("规则螺旋的运行比例（8 个种子）"); axs[0].set_ylim(-0.05, 1.05)
    axs[1].set_ylabel("原基间隔的变异系数"); axs[1].axhline(0.22, color="gray", ls=":"); axs[1].text(0.05, 0.225, "eLife 2020 估计 0.22", fontsize=8, color="gray")
    for a in axs:
        a.set_xlabel("记忆时间常数 τ_M（模型时间；螺旋的原基间隔约 16–20）"); a.legend(frameon=False, fontsize=8)
    fig.suptitle("时间积分放在回路内：亚临界时适度积分使叶序更规则，超临界时破坏叶序", fontsize=12)
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig); print("saved", out)


def make_gif(rc=3.5, seed=1, out="out/spiral.gif", t0=300.0, t1=460.0, dt=2.0):
    import imageio.v2 as imageio
    sim = Sim(dict(OP, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0, t_end=t1, mesh_seed=seed, seed=seed, snap_dt=dt)).run()
    frames = []
    snaps = [s for s in sim.snaps if s["t"] >= t0]
    vmax = np.percentile(np.concatenate([s["A"] for s in snaps]), 99.5)
    for s in snaps:
        fig, ax = plt.subplots(figsize=(5.6, 5.6))
        viz.draw_tissue(ax, s["pts"], s["A"], s["prim"], sim.p, 0, vmax, pin=s["pin"])
        ax.set_title(f"t = {s['t']:.0f}   白箭头: PIN1 平均方向   编号: 原基产生顺序", fontsize=9)
        fig.tight_layout(); fig.canvas.draw()
        frames.append(np.asarray(fig.canvas.buffer_rgba())[:, :, :3].copy()); plt.close(fig)
    imageio.mimsave(out, frames, duration=0.12, loop=0)
    print("saved", out, len(frames), "frames")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "types":
        fig_types()
    elif cmd == "phase":
        fig_phase()
    elif cmd == "tau":
        fig_tau()
    elif cmd == "gif":
        make_gif()
        make_gif(rc=6.0, seed=2, out="out/decussate.gif")
