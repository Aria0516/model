"""Regime figure: why the Smith-type operating point is noisy and what makes the pattern regular."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import figs  # noqa: F401  (font setup)
from lin import analyse
from model import DEFAULT

if __name__ == "__main__":
    fig, axs = plt.subplots(1, 2, figsize=(13.5, 4.6), gridspec_kw=dict(width_ratios=[1, 1.15]))
    ax = axs[0]
    levels = np.linspace(1.0, 8.0, 57)
    for b, col, lab in ((3.0, "#D55E00", "b = 3（Smith 2006 的取值）"), (2.0, "#009E73", "b = 2.0（本模型工作点）")):
        p = dict(DEFAULT); p["b"] = b
        lam = [analyse(p, A_level=float(a))[1] for a in levels]
        ax.plot(levels, lam, color=col, lw=2, label=lab)
    ax.axhline(0, color="k", lw=0.7)
    ax.axvspan(3.9, 4.3, color="#BBBBBB", alpha=0.5, lw=0); ax.text(4.35, 6.3, "无原基时\n环内水平", fontsize=8, va="top")
    ax.axvline(3.3, color="k", ls="--", lw=0.8); ax.text(3.25, 7.0, "起始阈值", fontsize=8, ha="right")
    ax.set_xlabel("局部生长素水平"); ax.set_ylabel("均匀态的最大增长率（>0 表示自发成峰）")
    ax.set_ylim(-1.0, 7.5); ax.legend(frameon=False, loc="upper left", fontsize=9, bbox_to_anchor=(0.0, 0.8))
    ax.set_title("运输反馈是否自发成核，取决于增益与局部生长素水平", fontsize=10)

    ax = axs[1]
    steps = ["Smith 型工作点\n(b=3，全域产生)", "环外低产生\n汇范围 3", "再降增益至\n亚临界 (b=2)", "再加回路内\n时间积分 τ=5"]
    f_alpha = [[0.57, 0.58], [0.87, 0.85], [0.90, 0.91, 0.73, 0.85], [0.98, 1.00, 0.94, 0.98, 0.95]]
    f_perm = [[0.24, 0.25], [0.07, 0.04], [0.00, 0.00, 0.12, 0.04], [0.00, 0.00, 0.00, 0.00, 0.00]]
    reg = ["0/8", "5–6/8", "3/6–6/8", "6/6、8/8"]
    for k, (fa, fp) in enumerate(zip(f_alpha, f_perm)):
        ax.bar(k - 0.18, np.mean(fa), width=0.34, color="#009E73"); ax.scatter([k - 0.18] * len(fa), fa, color="k", s=12, zorder=3)
        ax.bar(k + 0.18, np.mean(fp), width=0.34, color="#D55E00"); ax.scatter([k + 0.18] * len(fp), fp, color="k", s=12, zorder=3)
        ax.text(k, 1.03, f"规则螺旋 {reg[k]}", ha="center", fontsize=9)
    ax.set_xticks(range(4)); ax.set_xticklabels(steps, fontsize=9); ax.set_ylim(0, 1.12)
    ax.set_ylabel("占全部相邻夹角的比例")
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color="#009E73"), plt.Rectangle((0, 0), 1, 1, color="#D55E00")],
              labels=["落在主导夹角 ±30° 内", "属于次序置换"], frameon=False, loc="center right", fontsize=9, bbox_to_anchor=(1.0, 0.55))
    ax.set_title("逐步改动的效果（黑点：各批 6–8 个种子的均值；发生环内半径 3.5–4）", fontsize=10)
    fig.tight_layout(); fig.savefig("out/fig_regime.png", dpi=110); plt.close(fig); print("saved out/fig_regime.png")
