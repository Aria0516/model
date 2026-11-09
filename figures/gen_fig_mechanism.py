#!/usr/bin/env python3
"""Generate a black-and-white SVG schematic of the current model design.

Content follows the current main line (model_mvp/detuned_v3/frozen_v3) and the
evidence table in 项目阶段性总结_20261101.md, section 5.
Panel A: spatial layout of the apex (top view + cross-section).
Panel B: regulatory loop. Solid box = literature/data support; dashed box =
phenomenological setting; † = parameter without measurement.

Standard library only. Render to PNG/PDF with a headless browser (see README
note at the bottom of this file).
"""

import re
from html import escape
from math import cos, pi, radians, sin
from pathlib import Path

W, H = 1940, 1200
OUT = Path(__file__).resolve().parent
FONT = ("'Noto Sans CJK SC','Source Han Sans SC','Microsoft YaHei','PingFang SC',"
        "'WenQuanYi Zen Hei',sans-serif")
INK = "#111111"
MID = "#555555"
SOFT = "#8a8a8a"
FILL = "#efefef"
FILL2 = "#d9d9d9"

out = []


# ---------- primitives ----------
def rich(s):
    """Escape text; `_{x}` becomes a subscript tspan."""
    parts = re.split(r"(_\{[^}]*\})", s)
    res = []
    for p in parts:
        if p.startswith("_{"):
            res.append(f'<tspan baseline-shift="sub" font-size="72%">{escape(p[2:-1])}</tspan>')
        else:
            res.append(escape(p))
    return "".join(res)


def text(x, y, s, size=18, anchor="middle", weight=400, fill=INK, italic=False):
    st = ' font-style="italic"' if italic else ""
    out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" '
               f'font-weight="{weight}" fill="{fill}"{st}>{rich(s)}</text>')


def label(x, y, s, size=15, anchor="middle"):
    """Edge label with a white halo so it stays readable over lines."""
    out.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{INK}" '
               f'stroke="white" stroke-width="5" paint-order="stroke" stroke-linejoin="round">{rich(s)}</text>')


def path(pts, dash=None, end="arrow", width=2.2, color=INK):
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    me = f' marker-end="url(#{end})"' if end else ""
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" '
               f'stroke-linejoin="round"{da}{me}/>')


# ---------- panel B: boxes ----------
BW, BH = 290, 124
COL = {"A": 900, "B": 1305, "C": 1710}
ROW = {1: 215, 2: 390, 3: 565, 4: 740, 5: 915}


class Box:
    def __init__(self, col, row, title, lines, src, dashed=False, state=False):
        self.x, self.y = COL[col], ROW[row]
        self.title, self.lines, self.src = title, lines, src
        self.dashed, self.state = dashed, state

    # anchor points
    def L(self, dy=0): return (self.x - BW / 2, self.y + dy)
    def R(self, dy=0): return (self.x + BW / 2, self.y + dy)
    def T(self, dx=0): return (self.x + dx, self.y - BH / 2)
    def B(self, dx=0): return (self.x + dx, self.y + BH / 2)

    def draw(self):
        x0, y0 = self.x - BW / 2, self.y - BH / 2
        da = ' stroke-dasharray="9 6"' if self.dashed else ""
        fill = FILL if self.state else "white"
        sw = 3.2 if self.state else 2
        out.append(f'<rect x="{x0}" y="{y0}" width="{BW}" height="{BH}" rx="10" fill="{fill}" '
                   f'stroke="{INK}" stroke-width="{sw}"{da}/>')
        n = len(self.lines)
        ty = self.y - BH / 2 + 34 + (2 - n) * 10
        text(self.x, ty, self.title, size=21, weight=700)
        for i, ln in enumerate(self.lines):
            text(self.x, ty + 27 + 23 * i, ln, size=16)
        text(self.x, self.y + BH / 2 - 12, self.src, size=13.5, fill=MID, italic=True)


def defs():
    out.append(f"""<defs>
<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>
<marker id="bar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="11" markerHeight="11" orient="auto">
  <path d="M5,0 L5,10" stroke="{INK}" stroke-width="2.6"/></marker>
<marker id="arrowSoft" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
  <path d="M0,0 L10,5 L0,10 z" fill="{MID}"/></marker>
<pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="8" height="8" fill="white"/><line x1="0" y1="0" x2="0" y2="8" stroke="{SOFT}" stroke-width="2.4"/></pattern>
<pattern id="dots" width="10" height="10" patternUnits="userSpaceOnUse">
  <rect width="10" height="10" fill="white"/><circle cx="5" cy="5" r="1.6" fill="{MID}"/></pattern>
</defs>""")


def panel_b():
    text(760, 72, "B  调控回路", size=26, anchor="start", weight=700)

    src = Box("A", 1, "外围产生生长素", ["源区位于发生环外 2 个细胞", "ρ_{far}†：按无原基时环内水平设定"],
              "Galvan-Ampudia 2020（定性）")
    A = Box("B", 1, "发生环生长素 A", ["产生、周转、扩散", "与极性运输共同决定"], "模型状态量", state=True)
    pin = Box("C", 1, "PIN1 向高生长素极化", ["指数型规则 b = 3", "每个细胞 PIN 总量有限"],
              "Smith 2006；Jönsson 2006；Sahlin 2009")
    M = Box("B", 2, "时间积分 M", ["泄漏积分，时长约 2–5 h"], "Galvan-Ampudia 2020")
    dr5 = Box("A", 2, "DR5 样读出 R", ["被动读出，不反馈", "滞后约 1 个原基间隔"], "Galvan-Ampudia 2020")
    th = Box("B", 3, "阈值起始", ["M ≥ θ_{rel}†·A_{0}", "且距已有原基 > 1.18 w"], "Smith 2006（阈值放置）")
    sec = Box("A", 3, "次级抑制场", ["起始约 1 个间隔后出现", "局部抬高起始阈值"], "Besnard 2014（AHP6）")
    prim = Box("B", 4, "原基（放置的对象）", ["足迹 w†、汇强度 η†", "极化线索 A_{q}†"], "唯象设定", dashed=True)
    inner = Box("B", 5, "内层与维管排出", ["原基把生长素送入内层", "交换 k_{v}†、饱和 K_{e}†、排出 η_{2}†"],
                "Bayer 2009；Deb 2015（定性）")

    # edges (drawn first so boxes sit on top)
    path([src.R(), A.L()])
    label((src.R()[0] + A.L()[0]) / 2, src.y - 12, "向心运输 κ_{c}†", size=14.5)

    path([A.R(-20), pin.L(-20)])
    label((A.R()[0] + pin.L()[0]) / 2, A.y - 30, "浓度定极性", size=14.5)
    path([pin.L(22), A.R(22)])
    label((A.R()[0] + pin.L()[0]) / 2, A.y + 46, "运输汇聚成峰", size=14.5)

    path([A.B(), M.T()])
    path([M.L(), dr5.R()], dash="3 5", end="arrowSoft", color=MID)
    path([M.B(), th.T()])
    path([th.B(), prim.T()])
    label(th.x + 12, (th.B()[1] + prim.T()[1]) / 2 + 6, "放置原基", size=14.5, anchor="start")
    path([prim.B(), inner.T()])
    label(prim.x + 12, (prim.B()[1] + inner.T()[1]) / 2 + 6, "排入内层", size=14.5, anchor="start")

    # primordium triggers the secondary field, which inhibits initiation
    path([prim.L(), (sec.x, prim.y), sec.B()])
    label(sec.x - 12, (sec.B()[1] + prim.y) / 2 + 6, "触发", size=14.5, anchor="end")
    path([sec.R(), th.L()], end="bar")
    label((sec.R()[0] + th.L()[0]) / 2, sec.y - 12, "抬高阈值", size=14.5)

    # polarity cue: primordium -> PIN
    path([prim.R(-18), (pin.x, prim.y - 18), pin.B()])
    label(pin.x + 12, ROW[3], "极化线索 A_{q}†", size=14.5, anchor="start")
    label(pin.x + 12, ROW[3] + 22, "（PIN 指向原基）", size=13.5, anchor="start")

    # sink: primordium -| ring auxin, routed outside on the right
    xr = pin.x + BW / 2 + 38
    ytop = A.y - BH / 2 - 44
    path([prim.R(22), (xr, prim.y + 22), (xr, ytop), (A.x, ytop), A.T()], end="bar")
    label((A.x + xr) / 2, ytop - 10, "汇：局部耗竭生长素 η†", size=14.5)

    for b in (src, A, pin, M, dr5, th, sec, prim, inner):
        b.draw()

    # background band
    y0 = 1010
    out.append(f'<rect x="750" y="{y0}" width="1150" height="62" rx="10" fill="url(#hatch)" '
               f'stroke="{INK}" stroke-width="2"/>')
    out.append(f'<rect x="770" y="{y0 + 12}" width="1110" height="38" rx="6" fill="white"/>')
    text(1325, y0 + 38, "背景：Voronoi 表皮细胞层均匀生长、分裂、外移；几何取自 21 个茎尖实测（1 单位 = 4.91 µm，≈ 1.6 h）",
         size=16.5)


# ---------- panel A: apex ----------
def panel_a():
    text(40, 72, "A  茎尖布局（俯视）", size=26, anchor="start", weight=700)
    cx, cy = 285, 380
    r_cz, r_c, r_p, r_s1, r_s2, r_out = 63, 100, 135, 165, 190, 236

    def circ(r, **kw):
        attrs = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in kw.items())
        out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" {attrs}/>')

    circ(r_out, fill="white", stroke=SOFT, stroke_width=1.5, stroke_dasharray="4 5")
    # source zone (dotted annulus)
    out.append(f'<path d="M {cx + r_s2} {cy} A {r_s2} {r_s2} 0 1 0 {cx - r_s2} {cy} A {r_s2} {r_s2} 0 1 0 {cx + r_s2} {cy} '
               f'M {cx + r_s1} {cy} A {r_s1} {r_s1} 0 1 1 {cx - r_s1} {cy} A {r_s1} {r_s1} 0 1 1 {cx + r_s1} {cy} Z" '
               f'fill="url(#dots)" fill-rule="evenodd" stroke="{INK}" stroke-width="1.2"/>')
    # generative ring
    out.append(f'<path d="M {cx + r_p} {cy} A {r_p} {r_p} 0 1 0 {cx - r_p} {cy} A {r_p} {r_p} 0 1 0 {cx + r_p} {cy} '
               f'M {cx + r_c} {cy} A {r_c} {r_c} 0 1 1 {cx - r_c} {cy} A {r_c} {r_c} 0 1 1 {cx + r_c} {cy} Z" '
               f'fill="url(#hatch)" fill-rule="evenodd" stroke="{INK}" stroke-width="1.6"/>')
    circ(r_cz, fill=FILL2, stroke=INK, stroke_width=1.6)

    # inward transport arrows
    for a in (30, 160, 250, 295):
        t = radians(a)
        p1 = (cx + (r_s1 - 4) * cos(t), cy - (r_s1 - 4) * sin(t))
        p2 = (cx + (r_p + 6) * cos(t), cy - (r_p + 6) * sin(t))
        path([p1, p2], width=2.4)

    # primordia on a 137.5 deg spiral; older ones further out
    ang0 = 65
    spec = [("P0", r_c + 17, 0, 7), ("P1", 155, 1, 11), ("P2", 186, 2, 14), ("P3", 214, 3, 17)]
    for name, rr, k, size in spec:
        t = radians(ang0 + 137.5 * k)
        px, py = cx + rr * cos(t), cy - rr * sin(t)
        if k == 1:
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="40" fill="none" stroke="{INK}" '
                       f'stroke-width="1.6" stroke-dasharray="7 5"/>')
            fx, fy = px + 44 * cos(radians(-30)), py - 44 * sin(radians(-30))
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{size}" fill="{INK}"/>')
        lx, ly = cx + (rr + size + 20) * cos(t), cy - (rr + size + 20) * sin(t)
        text(lx, ly + 6, name, size=17, weight=700)
    # footprint callout
    t1 = radians(ang0 + 137.5)
    p1x, p1y = cx + 155 * cos(t1), cy - 155 * sin(t1)
    path([(p1x - 36, p1y + 28), (p1x - 80, p1y + 92)], end=None, width=1.3, color=MID)
    text(p1x - 82, p1y + 112, "足迹 w†", size=15.5)

    # growth arrow
    t = radians(-38)
    path([(cx + 200 * cos(t), cy - 200 * sin(t)), (cx + 272 * cos(t), cy - 272 * sin(t))], width=2.4)
    text(cx + 286 * cos(t) - 10, cy - 286 * sin(t) + 26, "生长外移", size=15.5, anchor="start")

    # zone labels in a column on the right, with leader lines
    lx = 556
    items = [
        (r_cz * 0.6, 40, 250, "中央区", ["PIN 0.2 倍", "本地合成 ρ_{in}†"]),
        ((r_c + r_p) / 2, 8, 360, "发生环", ["原基在此起始", "环宽†"]),
        ((r_s1 + r_s2) / 2, -4, 470, "源区", ["外围产生生长素"]),
    ]
    for rr, a, yy, name, subs in items:
        t = radians(a)
        px, py = cx + rr * cos(t), cy - rr * sin(t)
        path([(px, py), (lx - 10, yy - 6)], end=None, width=1.2, color=MID)
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.5" fill="{INK}"/>')
        text(lx, yy, name, size=18, anchor="start", weight=700)
        for k, sub in enumerate(subs):
            text(lx, yy + 22 + 20 * k, sub, size=14.5, anchor="start", fill=MID)
    text(cx, cy + r_out + 40, "箭头：向心极性运输（κ_{c}†）", size=15.5)

    # ---- cross-section ----
    y = 850
    text(40, y - 50, "茎尖纵切（示意）", size=20, anchor="start", weight=700)
    x0, x1 = 70, 650
    xp = 470                      # primordium position
    # epidermis L1
    out.append(f'<path d="M {x0} {y} L {xp - 70} {y} Q {xp} {y - 70} {xp + 70} {y} L {x1} {y} '
               f'L {x1} {y + 34} L {xp + 70} {y + 34} Q {xp} {y - 34} {xp - 70} {y + 34} L {x0} {y + 34} Z" '
               f'fill="url(#hatch)" stroke="{INK}" stroke-width="1.6"/>')
    text(x0 + 8, y - 12, "表皮 L1（模型主体）", size=15.5, anchor="start")
    # inner layer
    out.append(f'<rect x="{x0}" y="{y + 34}" width="{x1 - x0}" height="84" fill="{FILL}" stroke="{INK}" stroke-width="1.4"/>')
    text(x0 + 8, y + 82, "内层：横向扩散", size=15.5, anchor="start")
    # exchange arrows
    for xx in (190, 300):
        path([(xx, y + 6), (xx, y + 60)], width=1.8)
        path([(xx + 14, y + 60), (xx + 14, y + 6)], width=1.8)
    label(245, y + 112, "交换 k_{v}†", size=14.5)
    # primordium sink into inner layer
    path([(xp, y - 20), (xp, y + 78)], width=3)
    label(xp + 10, y + 64, "汇入内层", size=14.5, anchor="start")
    # vasculature
    out.append(f'<rect x="{xp - 22}" y="{y + 118}" width="44" height="82" fill="{FILL2}" stroke="{INK}" stroke-width="1.4"/>')
    path([(xp, y + 120), (xp, y + 196)], width=2.4)
    text(xp + 34, y + 172, "维管排出 η_{2}†", size=15.5, anchor="start")
    text(xp, y - 50, "原基", size=16, weight=700)


def legend():
    y = 1128
    x = 40
    out.append(f'<rect x="{x}" y="{y - 22}" width="34" height="24" rx="4" fill="white" stroke="{INK}" stroke-width="2"/>')
    text(x + 44, y - 3, "有文献或数据依据", size=16, anchor="start")
    x += 210
    out.append(f'<rect x="{x}" y="{y - 22}" width="34" height="24" rx="4" fill="white" stroke="{INK}" '
               f'stroke-width="2" stroke-dasharray="6 4"/>')
    text(x + 44, y - 3, "唯象设定", size=16, anchor="start")
    x += 150
    text(x, y - 3, "† 参数无测量值", size=16, anchor="start")
    x += 160
    path([(x, y - 10), (x + 46, y - 10)])
    text(x + 56, y - 3, "促进", size=16, anchor="start")
    x += 120
    path([(x, y - 10), (x + 46, y - 10)], end="bar")
    text(x + 56, y - 3, "抑制", size=16, anchor="start")
    x += 120
    path([(x, y - 10), (x + 46, y - 10)], dash="3 5", end="arrowSoft", color=MID)
    text(x + 56, y - 3, "被动读出", size=16, anchor="start")
    x += 150
    text(x, y - 3, "叶序的角度、间隔和手性均未写入模型，由动力学自发产生。", size=16, anchor="start", fill=MID)


def main():
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
               f'font-family="{FONT}">')
    defs()
    out.append(f'<rect width="{W}" height="{H}" fill="white"/>')
    out.append(f'<line x1="725" y1="50" x2="725" y2="1080" stroke="{FILL2}" stroke-width="1.5"/>')
    panel_a()
    panel_b()
    legend()
    out.append("</svg>")
    svg = "\n".join(out)
    (OUT / "fig_model_mechanism.svg").write_text(svg, encoding="utf-8")
    html = (f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}'
            f'@page{{size:{W}px {H}px;margin:0}}</style></head><body>{svg}</body></html>')
    (OUT / "fig_model_mechanism.html").write_text(html, encoding="utf-8")
    print("wrote", OUT / "fig_model_mechanism.svg")


if __name__ == "__main__":
    main()

# Render (any headless Chromium), e.g. with Playwright:
#   page.set_viewport_size(1840x1200); page.goto(file://.../fig_model_mechanism.html)
#   page.screenshot(path="fig_model_mechanism.png", device_scale_factor=2)
#   page.pdf(path="fig_model_mechanism.pdf", width="1840px", height="1200px")
