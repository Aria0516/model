"""Phase diagram (three panels) and regime-comparison figure."""
import sys
from collections import Counter, defaultdict

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from figs import COL, ZH, load


def regular(r):
    return r["pattern"] != "none" and not r["pattern"].endswith("~")


def base(r):
    return r["pattern"].rstrip("~")


def fig_phase(path="out/e11_grid.jsonl", out="out/fig_phase.png"):
    res = load(path)
    by = defaultdict(list)
    for r in res:
        by[(r["over"]["w"], r["over"]["R_c"])].append(r)
    ws = sorted({k[0] for k in by}); rcs = sorted({k[1] for k in by})
    fig = plt.figure(figsize=(16.5, 5.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.35, 1, 1])
    ax = fig.add_subplot(gs[0])
    for (w, rc), rs in by.items():
        name = Counter(base(r) for r in rs).most_common(1)[0][0]
        reg = np.mean([regular(r) for r in rs])
        x, y = rcs.index(rc), ws.index(w)
        ax.add_patch(plt.Rectangle((x - 0.47, y - 0.45), 0.94, 0.9, color=COL.get(name, "#999999"), alpha=0.2 + 0.8 * reg, lw=0))
        j2 = [r for r in rs if r.get("jugacy", 1) >= 2]
        lab = "成对" if len(j2) * 2 > len(rs) else f"{np.median([r['alpha'] for r in rs if 'alpha' in r]):.0f}°"
        ax.text(x, y, f"{lab}\n{sum(regular(r) for r in rs)}/{len(rs)}", ha="center", va="center", fontsize=8)
    ax.set_xticks(range(len(rcs))); ax.set_xticklabels([f"{v:g}" for v in rcs]); ax.set_yticks(range(len(ws))); ax.set_yticklabels([f"{v:g}" for v in ws])
    ax.set_xlim(-0.6, len(rcs) - 0.4); ax.set_ylim(-0.6, len(ws) - 0.4)
    ax.set_xlabel("发生环内半径 R_c（细胞直径）"); ax.set_ylabel("原基汇的范围 w（细胞直径）")
    hs = [plt.Line2D([], [], marker="s", ls="", ms=11, color=COL[k], label=ZH[k]) for k in ("distichous", "intermediate", "spiral", "decussate", "other")]
    ax.legend(handles=hs, ncol=5, loc="upper center", bbox_to_anchor=(0.5, 1.14), frameon=False, fontsize=9)
    ax.set_title("格内：主导夹角，规则运行数/种子数（颜色越实越规则）", fontsize=9, y=-0.24)

    ax = fig.add_subplot(gs[1]); ax2 = fig.add_subplot(gs[2])
    for r in res:
        if r["pattern"] == "none":
            continue
        o = r["over"]; x = (o["R_c"] + 1.0) / o["w"]; name = base(r); ok = regular(r)
        kw = dict(s=30, color=COL.get(name, "#999999"), alpha=0.95 if ok else 0.25, edgecolors="k" if ok else "none", linewidths=0.4)
        if r.get("jugacy", 1) >= 2:
            ax.scatter(x, r["rot_frac"] * 180.0, marker="D", **kw)
            ax2.scatter(x, r["G"] / r["jugacy"], marker="D", **kw)     # per organ
        else:
            ax.scatter(x, r["alpha"], marker="o", **kw)
            ax2.scatter(x, r["G"], marker="o", **kw)
    for a, lab in ((180, "180°"), (137.5, "137.5°"), (90, "90°")):
        ax.axhline(a, color="r", ls="--", lw=0.7); ax.text(4.95, a + 1.5, lab, color="r", fontsize=8, ha="right")
    ax.set_xlabel("环中线半径 / 汇范围  (R_c+1)/w"); ax.set_ylabel("夹角（度）")
    ax.set_title("圆点：相邻原基的主导夹角；菱形：相邻两节之间的转角", fontsize=9)
    ax2.axhline(0.23, color="gray", ls=":", lw=0.9); ax2.text(4.95, 0.24, "拟南芥花序 0.23（eLife 2020）", fontsize=8, color="gray", ha="right")
    ax2.set_xlabel("环中线半径 / 汇范围  (R_c+1)/w"); ax2.set_ylabel("每个原基对应的径向比对数 G")
    ax2.set_title("G 为自发出现的量，未作设定", fontsize=9)
    for a in (ax, ax2):
        a.set_xlim(0.7, 5.1)
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig); print("saved", out)


if __name__ == "__main__":
    fig_phase()
