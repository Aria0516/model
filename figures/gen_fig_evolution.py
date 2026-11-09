#!/usr/bin/env python3
"""Generate a black-and-white SVG timeline of how the model was developed.

Content follows 项目阶段性总结_20261101.md (sections 3-4, 8) and the
RESULTS.md files it links. Each row is one step on the main line: what was
changed, what it was aimed at, and what came out. The right column lists
mechanisms that were tested but not merged.

Set SHOW_FOLDERS = False to hide the internal folder names (e.g. for the
opening report, which avoids internal version names).

Standard library only; render to PNG/PDF with a headless browser
(see the note at the bottom of gen_fig_mechanism.py).
"""

import re
from html import escape
from pathlib import Path

SHOW_FOLDERS = True

W, H = 1940, 1190
OUT = Path(__file__).resolve().parent
FONT = ("'Noto Sans CJK SC','Source Han Sans SC','Microsoft YaHei','PingFang SC',"
        "'WenQuanYi Zen Hei',sans-serif")
INK, MID, SOFT, FILL = "#111111", "#555555", "#9a9a9a", "#efefef"

out = []


def rich(s):
    parts = re.split(r"(_\{[^}]*\})", s)
    return "".join(f'<tspan baseline-shift="sub" font-size="72%">{escape(p[2:-1])}</tspan>'
                   if p.startswith("_{") else escape(p) for p in parts)


def text(x, y, s, size=16, anchor="start", weight=400, fill=INK, italic=False):
    st = ' font-style="italic"' if italic else ""
    out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
               f'font-weight="{weight}" fill="{fill}"{st}>{rich(s)}</text>')


def rect(x, y, w, h, dashed=False, fill="white", sw=2, rx=10):
    da = ' stroke-dasharray="9 6"' if dashed else ""
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
               f'stroke="{INK}" stroke-width="{sw}"{da}/>')


def line(x1, y1, x2, y2, dash=None, arrow=False, color=INK, width=2):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    me = ' marker-end="url(#arrow)"' if arrow else ""
    out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{da}{me}/>')


def result_line(x, y, s):
    """Lines starting with + / - get a gain/problem glyph."""
    if s[:1] in "+-":
        if s[0] == "+":
            out.append(f'<circle cx="{x + 7}" cy="{y - 6}" r="7" fill="{INK}"/>')
            line(x + 3, y - 6, x + 11, y - 6, color="white", width=2)
            line(x + 7, y - 10, x + 7, y - 2, color="white", width=2)
        else:
            out.append(f'<circle cx="{x + 7}" cy="{y - 6}" r="6.5" fill="white" stroke="{INK}" stroke-width="1.6"/>')
            line(x + 3, y - 6, x + 11, y - 6, width=1.8)
        text(x + 22, y, s[1:].strip())
    else:
        text(x, y, s)


# ---------- content ----------
STEPS = [
    dict(title="基础模型", folder="frozen_v1",
         why="出发点：Smith 2006、Jönsson 2006",
         change=["细胞层生长分裂；PIN 向高生长素极化", "原基作汇与极化线索；时间积分越阈起始",
                 "另加两个唯象部件：全环次级场、跟随后定位"],
         result=["+只改发生环大小，依次得二列互生、螺旋、交互对生",
                 "+加唯象部件后 P1–P5 离散 5.2–5.4°（实测 6.7°）"]),
    dict(title="留出检验", folder="heldout",
         why="检验第 1 步",
         change=["10 项文献结果，判据在运行前写定"],
         result=["通过 3 项，部分通过 1，无法判定 1，不通过 5",
                 "-关掉极性运输后仍产生原基（pin1、NPA 应无器官）",
                 "-去掉次级场叶序崩溃，远重于 ahp6"]),
    dict(title="生长素由运输供给", folder="v2_supply",
         why="针对：无运输仍有原基",
         change=["生长素改在外围产生", "加整体向心的 PIN 偏置 κ_{c}"],
         result=["+24 组中 20 组：关掉运输即不再产生原基",
                 "+中央区生长素为发生环的 0.98–1.76 倍",
                 "-叶序类型变得取决于起始方式"]),
    dict(title="加入内层", folder="v3_layer",
         why="针对：原基起始后不维持高生长素",
         change=["原基把生长素排入内层", "内层横向扩散、与表皮交换、维管排出"],
         result=["+原基起始后在阈值以上 ≥ 1 个间隔（11/16 组）",
                 "+DR5 样读出滞后 1–1.5 个间隔",
                 "-夹角 141–142°；交互对生不再出现"]),
    dict(title="冻结主线，标定尺度", folder="frozen_v2 · calib_v2 · 2026-10-14",
         why="合并前三步",
         change=["参数写定，哈希清单冻结", "几何取自 21 个茎尖：1 单位 = 4.91 µm"],
         result=["+起始半径 26–29 µm（实测 29.0 µm）",
                 "-过于规则：离散 3° 对实测 6.7°",
                 "-非规范夹角 0% 对实测 15%"]),
    dict(title="去掉按规则性挑选的设定", folder="detuned_v3 · 2026-10-19",
         why="针对：有序来自挑选的设定",
         change=["b 改用 Smith 的 3；去掉两个唯象部件", "次级场改为 AHP6 形式（Besnard 2014）",
                 "15 个未测参数抽样，120 组 × 2 个种子"],
         result=["-规则螺旋只占 11%，取决于 w、η、κ_{c}",
                 "-规则螺旋中离散 21°，平均夹角 141.2°",
                 "+未经调整即相符：间隔 13.8 h，同时起始 36%"]),
    dict(title="下一步（未开始）", folder="", next=True,
         why="针对：w、η、κ_{c} 没有测量值",
         change=["用 PIN1 极性数据确定 κ_{c}", "用 qDII 消耗区约束 w、η（需先确认）"],
         result=["在约束后的模型上重做留出检验"]),
]

BRANCHES = [
    ("PIN 量的随机差异", "noise_v3", ["模型需 σ = 0.32–0.48，实测 0.080", "→ 不是叶序不规则的来源"]),
    ("运河化", "canal_v4", ["排出通道自己起不来", "→ 位于 PIN1 汇聚点的下游"]),
    ("表皮自发成峰", "canal_v4", ["b = 2–6、κ_{c} = 0–1.5 均不成峰", "→ 与“无运输则无器官”相矛盾"]),
    ("类 MP 响应吸引 PIN", "mp_v5", ["原基位置可自发产生", "→ 但时序失序，规则 0–1/16"]),
    ("WUS 门控生长素响应", "wus_v6 · 2026-10-28", ["只写了方案，未运行", "→ 留待学位论文后期"]),
]


def main():
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
               f'font-family="{FONT}">')
    out.append(f"""<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9"
 orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker></defs>""")
    out.append(f'<rect width="{W}" height="{H}" fill="white"/>')
    text(40, 62, "模型发展过程：每一步改动都针对上一步暴露的问题", size=27, weight=700)

    x0, x1 = 128, 1272                 # row box
    xc, xr = 470, 850                  # change / result columns
    y, rh, gap = 104, 124, 15
    spine_x = 76
    text(xc, y - 10, "改动", size=15, fill=MID, weight=700)
    text(xr, y - 10, "结果", size=15, fill=MID, weight=700)
    y += 6
    centers = []
    for i, s in enumerate(STEPS):
        nxt = s.get("next", False)
        rect(x0, y, x1 - x0, rh, dashed=nxt, fill="white")
        cy = y + rh / 2
        centers.append(cy)
        # spine node
        if i > 0:
            line(spine_x, centers[i - 1] + 22, spine_x, cy - 24, arrow=True, dash="6 5" if nxt else None)
        fill = "white" if nxt else INK
        tcol = INK if nxt else "white"
        da = ' stroke-dasharray="4 3"' if nxt else ""
        out.append(f'<circle cx="{spine_x}" cy="{cy}" r="21" fill="{fill}" stroke="{INK}" stroke-width="2"{da}/>')
        text(spine_x, cy + 7, str(i + 1), size=20, anchor="middle", weight=700, fill=tcol)
        # title column
        text(x0 + 20, y + 44, s["title"], size=21, weight=700)
        if SHOW_FOLDERS and s["folder"]:
            text(x0 + 20, y + 70, s["folder"], size=13.5, fill=SOFT)
        # change column
        line(xc - 18, y + 14, xc - 18, y + rh - 14, color="#cccccc", width=1.2)
        text(xc, y + 28, s["why"], size=14.5, fill=MID, italic=True)
        for k, c in enumerate(s["change"]):
            text(xc, y + 54 + 24 * k, c)
        # result column
        line(xr - 18, y + 14, xr - 18, y + rh - 14, color="#cccccc", width=1.2)
        n = len(s["result"])
        ry = y + rh / 2 - 12 * (n - 1) + 6
        for k, r in enumerate(s["result"]):
            result_line(xr, ry + 26 * k, r)
        y += rh + gap

    # ---------- side branches ----------
    bx, bw = 1340, 560
    text(bx, 98, "旁支：在冻结主线上单独试验，未并入", size=20, weight=700)
    by, bh, bgap = 120, 128, 16
    # connector from rows 5-6 to the branch column
    ya, yb = centers[4], centers[5]
    xm = 1306
    line(x1, ya, xm, ya, dash="6 5")
    line(x1, yb, xm, yb, dash="6 5")
    line(xm, ya, xm, yb, dash="6 5")
    last = by + (len(BRANCHES) - 1) * (bh + bgap) + bh / 2
    line(xm, by + bh / 2, xm, max(last, yb), dash="6 5")
    for i, (title, folder, lines) in enumerate(BRANCHES):
        yy = by + i * (bh + bgap)
        rect(bx, yy, bw, bh, dashed=True)
        line(xm, yy + bh / 2, bx, yy + bh / 2, dash="6 5", arrow=True)
        text(bx + 20, yy + 36, title, size=19, weight=700)
        if SHOW_FOLDERS:
            text(bx + bw - 18, yy + 36, folder, size=13.5, anchor="end", fill=SOFT)
        for k, ln in enumerate(lines):
            text(bx + 20, yy + 68 + 26 * k, ln)

    # ---------- legend ----------
    ly = H - 42
    rect(40, ly - 20, 34, 24, rx=4)
    text(84, ly - 2, "已完成", size=16)
    rect(170, ly - 20, 34, 24, dashed=True, rx=4)
    text(214, ly - 2, "未并入主线 / 未开始", size=16)
    result_line(420, ly - 2, "+进展")
    result_line(530, ly - 2, "-问题或代价")
    text(700, ly - 2, "斜体灰字：这一步针对的问题。数字取自各目录 RESULTS.md 与 2026-11-01 阶段性总结。",
         size=15, fill=MID)

    out.append("</svg>")
    svg = "\n".join(out)
    (OUT / "fig_model_evolution.svg").write_text(svg, encoding="utf-8")
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}'
            f'@page{{size:{W}px {H}px;margin:0}}</style></head><body>{svg}</body></html>')
    (OUT / "fig_model_evolution.html").write_text(html, encoding="utf-8")
    print("wrote", OUT / "fig_model_evolution.svg")


if __name__ == "__main__":
    main()
