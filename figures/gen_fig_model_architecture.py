#!/usr/bin/env python3
"""Generate the architecture diagram of the auxin-PIN1 phyllotaxis model (main line v3) as SVG.

Uses only the Python standard library, like gen_fig_dispersion.py. The PNG and PDF next to the
SVG were rendered from it with headless Chromium.

What the boxes and arrows show is taken from the code, not from memory:
  model_mvp/detuned_v3/frozen_v3/model.py        epidermis, PIN allocation, primordia, M, R, initiation
  model_mvp/detuned_v3/frozen_v3/layer.py        inner layer, saturable transfer, vascular drain, ring ramp
  model_mvp/detuned_v3/frozen_v3/mainline_v3.py  fixed values (b = 3, instant commit, read-out)
  model_mvp/detuned_v3/PROTOCOL.md               the 15 sampled parameters (marked * or †)
  model_mvp/calib_v2/out/geometry.json           final ring radius 5.57 and 1 unit = 4.91 µm
"""

import re
from html import escape
from pathlib import Path

W, H = 1600, 1150
OUT = Path(__file__).resolve().parent / "fig_model_architecture.svg"

SANS = "'Microsoft YaHei','PingFang SC','Noto Sans CJK SC','Source Han Sans SC','WenQuanYi Zen Hei',sans-serif"
SERIF = "'Times New Roman','Liberation Serif','DejaVu Serif',serif"
INK = "#1A1A1A"
MID = "#555555"
SOFT = "#8A8A8A"
HEAD = "#E6E6E6"
PANEL = "#F6F6F6"
RING = "#BDBDBD"

DASH = "9 6"
DOT = "1.5 6"

# ---------------------------------------------------------------- rich text
# "$...$" is math (serif italic); inside or outside it, _{..} is a subscript and ^{..} a superscript.
TOKEN = re.compile(r"_\{([^}]*)\}|\^\{([^}]*)\}|([^_^]+|[_^])")


def rich(s, size):
    spans, cur = [], 0.0
    for k, part in enumerate(s.split("$")):
        math = k % 2 == 1
        for sub, sup, plain in TOKEN.findall(part):
            if plain:
                target, fs, txt, italic = 0.0, size, plain, math
            else:
                txt = sub or sup
                target = 0.30 * size if sub else -0.40 * size
                fs = 0.68 * size
                italic = math and (txt in ("ij",) or (len(txt) == 1 and txt.isalpha()))   # indices italic, labels upright
            attrs = []
            if abs(target - cur) > 1e-9:
                attrs.append(f'dy="{target - cur:.1f}"')
            cur = target
            if fs != size:
                attrs.append(f'font-size="{fs:.1f}"')
            if math:
                attrs.append(f'font-family="{SERIF}"')
            if italic:
                attrs.append('font-style="italic"')
            spans.append(f"<tspan {' '.join(attrs)}>{escape(txt)}</tspan>")
    return "".join(spans)


def text(x, y, s, size=21, anchor="start", weight=400, fill=INK):
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" fill="{fill}">{rich(s, size)}</text>')


# ---------------------------------------------------------------- shapes
def module(x, y, w, h, title, tag=None):
    """A model module: outlined box with a grey title strip; tag = literature source, right-aligned."""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="#FFFFFF" stroke="{INK}" stroke-width="2.2"/>',
           f'<path d="M{x + 1.1},{y + 44} V{y + 6} a5,5 0 0 1 5,-4.9 H{x + w - 6} a5,5 0 0 1 5,4.9 V{y + 44} Z" fill="{HEAD}"/>',
           f'<line x1="{x}" y1="{y + 44}" x2="{x + w}" y2="{y + 44}" stroke="{INK}" stroke-width="1.2"/>',
           text(x + 16, y + 30, title, 23, weight=700)]
    if tag:
        out.append(text(x + w - 14, y + 29, tag, 16, anchor="end", fill=MID))
    return "\n".join(out)


def panel(x, y, w, h, title=None, lines=(), size=19, gap=29):
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{PANEL}" stroke="{MID}" stroke-width="1.3"/>']
    ty = y + 28
    if title:
        out.append(text(x + 14, ty, title, 20, weight=700))
        ty += gap
    for s in lines:
        out.append(text(x + 14, ty, s, size))
        ty += gap
    return "\n".join(out)


def pill(cx, cy, w, h, label, size=22, passive=False):
    """A state variable (bold outline); passive = grey, not fed back into the dynamics."""
    stroke, fill, ink, sw = (SOFT, "#FFFFFF", MID, 1.6) if passive else (INK, "#FFFFFF", INK, 2.6)
    return (f'<rect x="{cx - w / 2}" y="{cy - h / 2}" width="{w}" height="{h}" rx="{h / 2}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"/>\n' + text(cx, cy + size * 0.36, label, size, "middle", 700, ink))


def arrow(pts, style="solid", both=False, grey=False, width=2.2):
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    dash = {"solid": "", "dash": f' stroke-dasharray="{DASH}"', "dot": f' stroke-dasharray="{DOT}" stroke-linecap="round"'}[style]
    m = "ahg" if grey else "ah"
    start = f' marker-start="url(#{m})"' if both else ""
    return (f'<path d="{d}" fill="none" stroke="{SOFT if grey else INK}" stroke-width="{width}"{dash}'
            f' marker-end="url(#{m})"{start}/>')


def label_bg(x, y, s, size=18, anchor="middle", fill=INK, pad_w=None):
    """Label on a white backing so it stays readable where it sits on a line."""
    w = pad_w if pad_w else 0.62 * size * len(s) + 16
    x0 = x - w / 2 if anchor == "middle" else (x if anchor == "start" else x - w)
    return (f'<rect x="{x0}" y="{y - size}" width="{w}" height="{size * 1.45}" fill="#FFFFFF"/>\n'
            + text(x, y, s, size, anchor, fill=fill))


# ---------------------------------------------------------------- figure
def build():
    g = []
    add = g.append

    # Row 1: geometry and growth -----------------------------------------------------------------
    gx, gy, gw, gh = 30, 22, 1540, 156
    add(module(gx, gy, gw, gh, "组织几何与生长", "尺度依据：21 个茎尖实测；Galvan-Ampudia 2020"))
    cx, cy = 118, 122                                                     # zone sketch, top view
    add(f'<circle cx="{cx}" cy="{cy}" r="50" fill="none" stroke="{MID}" stroke-width="1.4" stroke-dasharray="3 4"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="41" fill="none" stroke="{MID}" stroke-width="1"/>')
    for r in (45, 48):
        add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{SOFT}" stroke-width="1" stroke-dasharray="1 3"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="33" fill="{RING}" stroke="{INK}" stroke-width="1.2"/>')
    add(f'<circle cx="{cx}" cy="{cy}" r="19" fill="#FFFFFF" stroke="{INK}" stroke-width="1.2"/>')
    add(text(196, 90, "表皮 Voronoi 细胞层：均匀生长 $γ$，细胞分裂，越过外缘后移出", 20))
    add(text(196, 122, "分区（俯视，左图）：中央区（白）｜发生环（灰）｜外围源区（点线）", 20))
    add(text(196, 154, "起始方式：发生环由小长大，内半径 $R_{c}$ 2 → 5.57（由实测 CLV3 区半径换算）", 20))
    add(text(1556, 122, "1 长度单位 ≈ 1 个细胞 = 4.91 µm", 18, "end", fill=MID))
    add(text(1556, 154, "1 时间单位 ≈ 1.6 h", 18, "end", fill=MID))

    # Row 2: epidermis | read-out and initiation | primordia --------------------------------------
    ry, rh = 262, 418
    ex, ew = 30, 600
    add(module(ex, ry, ew, rh, "表皮层：生长素运输", "Smith 2006；Jönsson 2006"))
    add(panel(50, 324, 255, 86, "产生", ["外围 $ρ_{far}$，茎尖内 $ρ_{in}$*"]))
    add(panel(355, 324, 255, 86, "损失", ["周转 $μ$，生长稀释 2$γ$"]))
    ax, ay = 330, 466
    add(pill(ax, ay, 210, 56, "生长素 $A_{i}$", 23))
    add(arrow([(262, 410), (262, ay - 28)]))
    add(arrow([(398, ay - 28), (398, 410)]))
    add(panel(50, 560, 560, 104, "PIN1 分配 $P_{ij}$", [
        "每个细胞 PIN 总量有限（中央区 ×0.2），在各膜面间分配",
        "朝生长素高处与原基线索极化，$b$ = 3；整体向心偏置 $κ_{c}$*"], size=18, gap=27))
    add(arrow([(292, ay + 28), (292, 560)], "dash"))
    add(arrow([(368, 560), (368, ay + 28)]))
    add(label_bg(282, 528, "极化依据", 17, "end", pad_w=86))
    add(label_bg(378, 528, "主动运输 $T$ + 扩散 $D$", 17, "start", pad_w=182))
    add(text(150, 530, "上梯度", 17, "middle", fill=MID))
    add(text(150, 551, "正反馈", 17, "middle", fill=MID))

    rx, rw = 690, 410
    add(module(rx, ry, rw, rh, "细胞读取与原基启动"))
    mx, my = rx + rw / 2, 346
    add(pill(mx, my, 230, 52, "时间整合 $M$", 22))
    add(text(mx, 405, "d$M$/d$t$ = ($A$ − $M$) / $τ_{M}$†", 19, "middle"))
    add(text(mx, 432, "$τ_{M}$ = 0 时即瞬时阈值", 17, "middle", fill=MID))
    add(arrow([(mx, 442), (mx, 470)], "dash"))
    add(panel(rx + 34, 470, rw - 54, 106, "启动判据", [
        "发生环内 $M$ − $I$ ≥ $Th$*", "且距已有原基 > $r_{ex}$"], size=19, gap=28))
    add(pill(mx, 618, 270, 42, "DR5 样读出 $R$（被动）", 18, passive=True))
    add(arrow([(mx - 113, my + 12), (rx + 16, my + 12), (rx + 16, 618), (mx - 135, 618)], "dash", grey=True, width=1.6))
    add(text(rx + 14, ry + rh - 12, "Galvan-Ampudia 2020", 16, fill=MID))

    px, pw = 1180, 390
    add(module(px, ry, pw, rh, "原基（放置的对象）"))
    plines = [
        "位置随组织外移",
        "足迹 exp(−$d^{2}$ / 2$w^{2}$)，$w$*",
        "汇 $η$*：表皮生长素送入内层",
        "极化线索 $A_{q}$*：PIN 指向原基",
        "次级场 $I$†：原基年龄 $a_{on}$–$a_{off}$",
        "　出现，范围 $w_{I}$（AHP6 型）",
        "维管排出 $η_{2}$*（作用于内层）",
    ]
    for i, s in enumerate(plines):
        add(text(px + 20, 346 + i * 41, s, 19))
    add(text(px + pw - 14, ry + rh - 12, "Smith 2006；Besnard 2014", 16, "end", fill=MID))

    # arrows between row-2 modules
    add(arrow([(ax + 105, ay), (660, ay), (660, my - 10), (mx - 114, my - 10)], "dash"))
    add(label_bg(660, 420, "$A_{i}$", 19, pad_w=36))
    add(arrow([(rx + rw - 20, 512), (px, 512)], "dash", width=2.8))
    add(label_bg((rx + rw + px) / 2, 500, "新原基", 18, pad_w=66))
    add(arrow([(px, 566), (rx + rw - 20, 566)], "dash"))
    add(label_bg((rx + rw + px) / 2, 556, "$I$，$r_{ex}$", 18, pad_w=70))

    # negative feedback: primordia drain the epidermis and redirect PIN (routed above row 2)
    add(arrow([(1260, ry), (1260, 236), (520, ry - 26), (520, ry)], "dash"))
    add(text(890, 224, "汇 $η$、极化线索 $A_{q}$：原基周围形成消耗区，决定新原基的间距（负反馈）", 18, "middle"))

    # geometry feeds the cell graph and carries primordia outward
    add(arrow([(150, gy + gh), (150, ry)], "dot"))
    add(text(162, 230, "细胞图", 17, fill=MID))
    add(arrow([(1500, gy + gh), (1500, ry)], "dot"))
    add(text(1488, 230, "原基外移", 17, "end", fill=MID))

    # Row 3: inner layer | outputs -----------------------------------------------------------------
    ly, lh = 768, 150
    add(module(ex, ly, ew, lh, "内层（表皮之下）", "Bayer 2009；Deb 2015"))
    add(pill(150, 862, 190, 50, "生长素 $A_{2}$", 21))
    add(text(268, 848, "横向扩散，周转 $μ$", 19))
    add(text(268, 882, "原基下方维管排出 $η_{2}$*", 19))
    add(arrow([(232, ry + rh), (232, ly)]))
    add(label_bg(244, 734, "原基处转运（可饱和 $K_{e}$*）", 17, "start", pad_w=218))
    add(arrow([(540, ry + rh), (540, ly)], both=True))
    add(label_bg(528, 734, "交换 $k_{v}$*", 17, "end", pad_w=84))

    ox, ow = 700, 870
    add(module(ox, ly, ow, lh, "输出与评价", "只与实测比较，不参与调参"))
    add(text(ox + 20, 848, "原基序列（起始时间、位置）→ 发散角、叶序类型、P1–P5 相对夹角离散、", 19))
    add(text(ox + 20, 882, "发生间隔变异系数、同时起始比例、径向比 $G$、起始半径", 19))
    add(arrow([(rx + rw - 38, 576), (rx + rw - 38, ly)], "dash"))
    add(label_bg(rx + rw - 50, 734, "起始事件", 17, "end", pad_w=80))

    # Legend -----------------------------------------------------------------------------------------
    y0 = 972
    add(f'<line x1="30" y1="{y0 - 22}" x2="1570" y2="{y0 - 22}" stroke="{RING}" stroke-width="1"/>')
    add(arrow([(40, y0 + 6), (100, y0 + 6)]))
    add(text(112, y0 + 12, "生长素物质流", 18))
    add(arrow([(270, y0 + 6), (330, y0 + 6)], "dash"))
    add(text(342, y0 + 12, "调控 / 信号", 18))
    add(arrow([(480, y0 + 6), (540, y0 + 6)], "dot"))
    add(text(552, y0 + 12, "几何 / 位置", 18))
    add(f'<rect x="690" y="{y0 - 10}" width="70" height="32" rx="16" fill="#FFFFFF" stroke="{INK}" stroke-width="2.6"/>')
    add(text(772, y0 + 12, "状态变量", 18))
    add(f'<rect x="884" y="{y0 - 10}" width="70" height="32" rx="16" fill="#FFFFFF" stroke="{SOFT}" stroke-width="1.6"/>')
    add(text(966, y0 + 12, "被动读出，不影响动力学", 18))
    add(text(40, y0 + 56, "* 无测量值：主线 v3 在预设范围内拉丁超立方抽样（120 组 × 2 个种子）。"
                          "　† 取值范围依据文献（$τ_{M}$：Galvan-Ampudia 2020；次级场：Besnard 2014），同样抽样。", 17, fill=MID))
    add(text(40, y0 + 90, "本图为主线 v3（model_mvp/detuned_v3/frozen_v3）。主线 v2 的不同之处：$b$ = 2；"
                          "原基位置先跟随局部最大区再固定（$τ_{c}$ = 2）；次级场即时出现、覆盖全环；参数取单一值。", 17, fill=MID))
    add(text(40, y0 + 124, "原基不是自发形成的，而是在判据满足时放置；没有任何发散角、发生间隔或手性写入模型。", 17, fill=MID))

    defs = (f'<defs>'
            f'<marker id="ah" viewBox="0 0 12 10" refX="11" refY="5" markerWidth="13" markerHeight="11" '
            f'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L12,5 L0,10 z" fill="{INK}"/></marker>'
            f'<marker id="ahg" viewBox="0 0 12 10" refX="11" refY="5" markerWidth="11" markerHeight="9" '
            f'markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0,0 L12,5 L0,10 z" fill="{SOFT}"/></marker>'
            f'</defs>')
    body = "\n".join(g)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'font-family="{SANS}">\n<rect width="{W}" height="{H}" fill="#FFFFFF"/>\n{defs}\n{body}\n</svg>\n')


if __name__ == "__main__":
    OUT.write_text(build(), encoding="utf-8")
    print(f"wrote {OUT}")
