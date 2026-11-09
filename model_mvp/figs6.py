"""Noise figure: secondary inhibitory field at the Arabidopsis-like plastochron ratio (N03)."""
import json
from collections import Counter

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import figs  # noqa: F401  (fonts)
from figs import COL, ZH

FIELD_ZH = {"no field": "无次级场", "k1.2 r25 life4": "全环场\n强 1.2 寿命 4", "k1.6 r25 life3": "全环场\n强 1.6 寿命 3",
            "k2.4 r14 life2": "宽场\n强 2.4 寿命 2", "k0.8 r5 life8": "局部场\n范围 5 寿命 8"}
POINT_ZH = {"spiral w3.0 Rc3.5": "螺旋点\nG≈0.59", "decussate w3.0 Rc6.0": "交互对生点\nG≈0.3", "lowG w2.0 Rc5.5": "拟南芥径向比\nG≈0.24",
            "lowerG w2.0 Rc7.0": "更低径向比\nG≈0.19", "whorl3-seeded w3.0 Rc9.0": "三轮生起始\nG≈0.2"}


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


if __name__ == "__main__":
    res = load("out/n03.jsonl")
    get = lambda pn, fn: [r for r in res if r["name"] == f"{pn} | {fn}" and r.get("pattern") != "none"]
    fig, axs = plt.subplots(1, 3, figsize=(17, 5.2), gridspec_kw=dict(width_ratios=[1.05, 0.9, 1.25]))

    ax = axs[0]
    pn = "lowG w2.0 Rc5.5"
    x = np.arange(len(FIELD_ZH))
    nonc = [100 * (1 - np.mean([r["f_alpha"] for r in get(pn, fn)])) for fn in FIELD_ZH]
    cv = [np.mean([r["gap_cv"] for r in get(pn, fn)]) for fn in FIELD_ZH]
    reg = [sum(not r["pattern"].endswith("~") for r in get(pn, fn)) for fn in FIELD_ZH]
    ax.bar(x, nonc, color="#D55E00", width=0.55)
    for k in range(len(x)):
        ax.text(x[k], nonc[k] + 0.8, f"{nonc[k]:.0f}%\n规则 {reg[k]}/16", ha="center", fontsize=8.5)
    for y, lab in ((15, "Besnard 2014 野生型 15%"), (37, "Besnard 2014 ahp6 突变体 37%")):
        ax.axhline(y, color="k", ls="--", lw=0.8)
        ax.text(len(x) - 0.45, y + 0.6, lab, ha="right", fontsize=8.5, bbox=dict(facecolor="w", edgecolor="none", pad=1.0, alpha=0.85))
    ax.set_xticks(x); ax.set_xticklabels(list(FIELD_ZH.values()), fontsize=8.5); ax.set_ylim(0, 44)
    ax.set_ylabel("非规范夹角所占比例（%）")
    ax.set_title("拟南芥径向比处：不符合主导夹角的比例（16 个种子）", fontsize=10)
    ax2 = ax.twinx(); ax2.plot(x, cv, "o-", color="#0072B2"); ax2.set_ylim(0, 0.7)
    ax2.set_ylabel("原基间隔变异系数（蓝线；点线为 eLife 2020 的 0.22）", color="#0072B2", fontsize=9)
    ax2.axhline(0.22, color="#0072B2", ls=":", lw=0.9); ax2.spines["right"].set_visible(True)

    ax = axs[1]
    ranks = np.arange(1, 7)
    clean = lambda rs: [r for r in rs if r.get("jugacy", 9) <= 1 and r["f_perm"] == 0 and r["f_other"] <= 0.03]
    for pn, fns, col, lab in (("spiral w3.0 Rc3.5", ["no field"], "#009E73", "螺旋点 G≈0.59，无次级场"),
                              ("lowG w2.0 Rc5.5", ["k1.2 r25 life4", "k1.6 r25 life3", "k2.4 r14 life2"], "#D55E00", "G≈0.24，加次级场")):
        rs = sum((clean(get(pn, fn)) for fn in fns), [])
        m = np.nanmean(np.array([r["rank"] for r in rs]), axis=0)
        ax.plot(ranks, m, "o-", color=col, label=f"{lab}（{len(rs)} 次无置换运行）")
    ax.plot(ranks, 3.6 * np.sqrt(ranks), "k:", label="论文的随机游走模型（每步 3.6°）")
    ax.axhline(6.7, color="k", ls="--", lw=0.8); ax.text(6.0, 6.9, "论文实测 P1–P5 平均离散 6.7°", ha="right", fontsize=8.5)
    ax.set_xlabel("与较老原基的序号差"); ax.set_ylabel("相对夹角的离散（度）"); ax.set_ylim(0, 19)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left"); ax.set_title("角度精度：与论文同一口径的统计", fontsize=10)

    ax = axs[2]
    pts = list(POINT_ZH); flds = ["no field", "k1.2 r25 life4", "k0.8 r5 life8"]
    wbar = 0.26
    for j, fn in enumerate(flds):
        for i, pn in enumerate(pts):
            rs = get(pn, fn)
            if not rs:
                continue
            c = Counter(r["pattern"] for r in rs if not r["pattern"].endswith("~"))
            bottom = 0.0
            for name, cnt in c.most_common():
                h = cnt / len(rs)
                ax.bar(i + (j - 1) * wbar, h, width=wbar * 0.92, bottom=bottom, color=COL.get(name, "#999999"),
                       edgecolor="k", linewidth=0.5, hatch=["", "//", ".."][j])
                bottom += h
    ax.set_xticks(range(len(pts))); ax.set_xticklabels(list(POINT_ZH.values()), fontsize=8.5); ax.set_ylim(0, 1.08)
    ax.set_ylabel("得到规则叶序的运行比例")
    hs = [plt.Rectangle((0, 0), 1, 1, facecolor="w", edgecolor="k", hatch=h) for h in ("", "//", "..")]
    hs += [plt.Rectangle((0, 0), 1, 1, color=COL[k]) for k in ("spiral", "decussate", "lucas", "tricussate")]
    ax.legend(hs, ["无次级场", "全环场", "局部场", ZH["spiral"], ZH["decussate"], ZH["lucas"], ZH["tricussate"]], frameon=False, fontsize=8.5,
              ncol=2, loc="upper right")
    ax.set_title("次级场的范围决定同一几何下得到螺旋还是对生", fontsize=10)
    fig.tight_layout(); fig.savefig("out/fig_noise.png", dpi=110); plt.close(fig); print("saved out/fig_noise.png")
