"""Module figure: radial auxin profile and PIN centripetal index for selected variants (E13)."""
from collections import defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figs import load
from figs2 import regular

SHOW = [("ref", "基线", "k"), ("M2 pin_cz0.3", "中央区低 PIN 外排", "#0072B2"),
        ("M2 kappa_c0.5", "向心极性偏置 0.5", "#56B4E9"), ("M3 src12", "老原基转为源", "#D55E00"),
        ("M2+M3 full", "三项合并", "#009E73")]


def fig_modules(path="out/e13.jsonl", out="out/fig_modules.png"):
    res = load(path)
    by = defaultdict(list)
    for r in res:
        by[r["name"].split("|")[0]].append(r)
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.6))
    for key, lab, col in SHOW:
        rs = [r for r in by[key] if "prof" in r]
        if not rs:
            continue
        prof = np.mean([r["prof"] for r in rs], axis=0); pin = np.mean([r["pin_in_free"] for r in rs], axis=0)
        prof, pin = prof[:-2], pin[:-2]                 # outermost bins are boundary artefacts
        x = np.arange(len(prof)) + 0.5
        axs[0].plot(x, prof, "-o", ms=3, color=col, label=lab)
        axs[1].plot(x, pin, "-o", ms=3, color=col, label=lab)
    for a in axs[:2]:
        a.axvspan(4.0, 6.0, color="#DDDDDD", alpha=0.6, lw=0); a.set_xlabel("到茎尖中心的距离（细胞直径；灰带为发生环）")
    axs[0].set_ylabel("时间平均生长素浓度"); axs[0].legend(frameon=False, fontsize=8)
    axs[1].axhline(0, color="gray", lw=0.6); axs[1].set_ylabel("PIN1 向心指数（+1 全部指向中心）")
    axs[1].set_title("仅统计不在原基范围内的细胞", fontsize=9)
    names = [k for k in by]
    f1 = [np.mean([r.get("f_alpha", 0) for r in by[k]]) for k in names]
    ok = [np.mean([regular(r) for r in by[k]]) for k in names]
    y = np.arange(len(names))[::-1]
    axs[2].barh(y, ok, color="#009E73", height=0.6)
    ZHN = {"ref": "基线", "M2 pin_cz0.3": "M2 中央区低 PIN 外排", "M2 pin_cz0.3 rho_cz6": "M2 低外排 + 中央区自产",
           "M2 kappa_c0.5": "M2 向心偏置 0.5（变为交互对生）", "M2 kappa_c1.0": "M2 向心偏置 1.0", "M2 pin_cz0.3+kc0.5": "M2 低外排 + 偏置 0.5",
           "M3 sink off only": "M3 老原基停止汇", "M3 src6": "M3 老原基转源（6）", "M3 src12": "M3 老原基转源（12）",
           "M3 src12 + kc0.5": "M3 转源 + 向心偏置（4/6 夹角约 125°）", "M2+M3 full": "M2 + M3 合并", "M2+M3 full kc1.0": "M2 + M3 合并，偏置 1.0",
           "M4 tauR5": "M4 被动读出 τ_R=5", "M4 tauR15": "M4 被动读出 τ_R=15"}
    axs[2].set_yticks(y); axs[2].set_yticklabels([ZHN.get(k, k) for k in names], fontsize=8); axs[2].set_xlim(0, 1.05)
    axs[2].set_xlabel("得到规则叶序（任一类型）的运行比例，6 个种子")
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig); print("saved", out)


if __name__ == "__main__":
    fig_modules()
