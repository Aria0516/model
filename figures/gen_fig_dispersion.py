#!/usr/bin/env python3
"""Generate a self-contained SVG schematic of the auxin dispersion relation.

This implementation uses only the Python standard library so that the figure is
reproducible even when matplotlib is unavailable. A headless browser can render
the generated HTML to PNG and vector PDF.
"""

from html import escape
from math import acos, cos, pi, sin, sqrt
from pathlib import Path


TP = 1.0
D = 0.2
r_A = 0.02
N = 24

WIDTH = 1480
HEIGHT = 1250
OUT_DIR = Path(__file__).resolve().parent

BLUE = "#0072B2"
SKY = "#56B4E9"
GREEN = "#009E73"
ORANGE = "#E69F00"
VERMILION = "#D55E00"
GRAY = "#68737D"
DARK = "#25313B"
LIGHT_GRID = "#DCE3E8"


def dispersion(q: float) -> float:
    return -r_A + (1.0 - cos(q)) * (TP * cos(q) - 2.0 * D)


def txt(x, y, value, size=22, fill=DARK, anchor="start", weight=400,
        rotate=None, italic=False):
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    style = "italic" if italic else "normal"
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-size="{size}" font-weight="{weight}" font-style="{style}" '
        f'fill="{fill}"{transform}>{escape(str(value))}</text>'
    )


def line(x1, y1, x2, y2, stroke=GRAY, width=2, dash=None, marker_end=None):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    marker_attr = f' marker-end="url(#{marker_end})"' if marker_end else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}"{dash_attr}{marker_attr}/>'
    )


def rect(x, y, w, h, fill="white", stroke="#D6DDE2", radius=18, width=2, opacity=1):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}" stroke-width="{width}"/>'
    )


def path(points, stroke=DARK, width=3, fill="none", opacity=1, close=False):
    if not points:
        return ""
    commands = [f'M {points[0][0]:.2f},{points[0][1]:.2f}']
    commands.extend(f'L {x:.2f},{y:.2f}' for x, y in points[1:])
    if close:
        commands.append("Z")
    return (
        f'<path d="{" ".join(commands)}" fill="{fill}" fill-opacity="{opacity}" '
        f'stroke="{stroke}" stroke-width="{width}" stroke-linejoin="round" '
        f'stroke-linecap="round"/>'
    )


def star_points(cx, cy, outer=15, inner=7, n=5):
    pts = []
    for k in range(2 * n):
        radius = outer if k % 2 == 0 else inner
        angle = -pi / 2 + k * pi / n
        pts.append((cx + radius * cos(angle), cy + radius * sin(angle)))
    return pts


def make_svg():
    q_star = acos(0.5 + D / TP)
    ell_star = 2.0 * pi / q_star
    lam_star = dispersion(q_star)

    # lambda(q)=0 -> TP*c^2-(TP+2D)c+(2D+r_A)=0, c=cos(q).
    disc = (TP + 2.0 * D) ** 2 - 4.0 * TP * (2.0 * D + r_A)
    c_small = ((TP + 2.0 * D) - sqrt(disc)) / (2.0 * TP)
    c_large = ((TP + 2.0 * D) + sqrt(disc)) / (2.0 * TP)
    q_low = acos(c_large)
    q_high = acos(c_small)

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">')
    s.append("""
    <defs>
      <marker id="arrow-green" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
        <path d="M0,0 L0,6 L9,3 z" fill="#009E73"/>
      </marker>
      <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
        <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#23313B" flood-opacity="0.10"/>
      </filter>
      <style>
        text { font-family: 'Microsoft YaHei','Noto Sans CJK SC','Segoe UI',Arial,sans-serif; }
      </style>
    </defs>
    """)
    s.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#FAFBFC"/>')
    s.append(txt(WIDTH / 2, 58, "生长素扰动的色散关系示意图", size=34, anchor="middle", weight=700))
    s.append(txt(WIDTH / 2, 91, "色散关系选择早期峰间距；阈值、原基汇和生长决定这些峰的后续命运", size=18, fill=GRAY, anchor="middle"))

    # Panel A card and plot coordinates.
    s.append('<g filter="url(#shadow)">')
    s.append(rect(55, 118, 1370, 585, fill="white", stroke="#E2E7EB", radius=22, width=1.5))
    s.append('</g>')
    s.append(txt(88, 161, "A  色散关系：哪些空间扰动会被 auxin-PIN 反馈放大？", size=24, weight=700))

    px, py, pw, ph = 165.0, 205.0, 1190.0, 410.0
    q_min, q_max = 0.0, pi / 2.0
    y_min, y_max = -0.46, 0.105

    def sx(q):
        return px + (q - q_min) / (q_max - q_min) * pw

    def sy(value):
        return py + (y_max - value) / (y_max - y_min) * ph

    # Unstable-band background.
    s.append(f'<rect x="{sx(q_low):.2f}" y="{py}" width="{sx(q_high)-sx(q_low):.2f}" height="{ph}" fill="{ORANGE}" fill-opacity="0.075"/>')

    # Grid, axes and tick labels.
    y_ticks = [-0.4, -0.3, -0.2, -0.1, 0.0, 0.1]
    for value in y_ticks:
        yy = sy(value)
        s.append(line(px, yy, px + pw, yy, stroke=LIGHT_GRID, width=1))
        s.append(txt(px - 15, yy + 7, f"{value:.1f}", size=17, fill=GRAY, anchor="end"))
    q_ticks = [(0, "0"), (pi / 6, "π/6"), (pi / 3, "π/3"), (pi / 2, "π/2")]
    for value, label in q_ticks:
        xx = sx(value)
        s.append(line(xx, py, xx, py + ph, stroke=LIGHT_GRID, width=1))
        s.append(txt(xx, py + ph + 29, label, size=18, fill=GRAY, anchor="middle"))
    s.append(line(px, py + ph, px + pw, py + ph, stroke=GRAY, width=2))
    s.append(line(px, py, px, py + ph, stroke=GRAY, width=2))
    zero_y = sy(0.0)
    s.append(line(px, zero_y, px + pw, zero_y, stroke="#7F8992", width=2))

    # Filled positive and negative parts of the curve.
    qs = [q_min + (q_max - q_min) * k / 700 for k in range(701)]
    curve = [(sx(q), sy(dispersion(q))) for q in qs]
    pos_qs = [q_low + (q_high - q_low) * k / 300 for k in range(301)]
    pos_poly = [(sx(q_low), zero_y)] + [(sx(q), sy(dispersion(q))) for q in pos_qs] + [(sx(q_high), zero_y)]
    s.append(path(pos_poly, stroke="none", width=0, fill=ORANGE, opacity=0.25, close=True))
    left_qs = [q_min + (q_low - q_min) * k / 90 for k in range(91)]
    left_poly = [(sx(q_min), zero_y)] + [(sx(q), sy(dispersion(q))) for q in left_qs] + [(sx(q_low), zero_y)]
    s.append(path(left_poly, stroke="none", width=0, fill=SKY, opacity=0.17, close=True))
    right_qs = [q_high + (q_max - q_high) * k / 180 for k in range(181)]
    right_poly = [(sx(q_high), zero_y)] + [(sx(q), sy(dispersion(q))) for q in right_qs] + [(sx(q_max), zero_y)]
    s.append(path(right_poly, stroke="none", width=0, fill=SKY, opacity=0.17, close=True))
    s.append(path(curve, stroke=DARK, width=4, fill="none"))

    # Allowed discrete modes on the 24-cell ring.
    for m in range(1, N // 4 + 1):
        q_m = 2.0 * pi * m / N
        lam_m = dispersion(q_m)
        color = VERMILION if lam_m > 0 else BLUE
        s.append(f'<circle cx="{sx(q_m):.2f}" cy="{sy(lam_m):.2f}" r="8" fill="{color}" stroke="white" stroke-width="2"/>')
        s.append(txt(sx(q_m), sy(lam_m) - 14, f"m={m}", size=14, fill=color, anchor="middle", weight=600))

    # Fastest mode and its annotation.
    qx, qy = sx(q_star), sy(lam_star)
    s.append(line(qx, py, qx, py + ph, stroke=GREEN, width=2, dash="8,7"))
    s.append(path(star_points(qx, qy, 18, 8), stroke="white", width=2, fill=GREEN, opacity=1, close=True))
    s.append(rect(900, 218, 410, 114, fill="#FFFFFF", stroke="#C8D2D9", radius=12, width=1.5))
    s.append(txt(920, 251, f"最快增长：q* = {q_star:.3f} rad/细胞", size=19, weight=700))
    s.append(txt(920, 282, f"ℓ* = 2π/q* = {ell_star:.2f} 个细胞", size=18, fill=GREEN, weight=600))
    s.append(txt(920, 311, f"λmax = {lam_star:.3f} /时间", size=18, fill=GREEN, weight=600))
    s.append(line(900, 278, qx + 12, qy + 5, stroke=GREEN, width=2, marker_end="arrow-green"))

    s.append(txt(sx(0.59), sy(0.031), "λ(q)>0：扰动放大 → 候选生长素峰", size=18, fill="#955200", anchor="middle", weight=600))
    s.append(txt(sx(1.33), sy(-0.30), "λ(q)<0：扰动衰减", size=18, fill=BLUE, anchor="middle", weight=600))

    # Formula and legend.
    s.append(rect(185, 530, 505, 73, fill="#F6F8F9", stroke="#D6DDE2", radius=10, width=1.2))
    s.append(txt(205, 559, "λ(q) = −rₐ +(1−cos q)(TP cos q−2D)", size=19, weight=600))
    s.append(txt(205, 587, "示意参数：TP=1，D=0.2，rₐ=0.02（非实验拟合值）", size=16, fill=GRAY))
    s.append(f'<circle cx="745" cy="557" r="8" fill="{VERMILION}" stroke="white" stroke-width="2"/>')
    s.append(txt(764, 564, "允许且增长的离散模态", size=16, fill=VERMILION))
    s.append(f'<circle cx="745" cy="585" r="8" fill="{BLUE}" stroke="white" stroke-width="2"/>')
    s.append(txt(764, 592, "允许但衰减的离散模态", size=16, fill=BLUE))
    s.append(txt(px + pw / 2, 674, "空间波数 q（rad/细胞；越大表示空间波长越短）", size=20, anchor="middle", weight=600))
    s.append(txt(92, py + ph / 2, "增长率 λ(q)（1/时间）", size=19, anchor="middle", weight=600, rotate=-90))

    # Panel B card.
    s.append('<g filter="url(#shadow)">')
    s.append(rect(55, 735, 1370, 435, fill="white", stroke="#E2E7EB", radius=22, width=1.5))
    s.append('</g>')
    s.append(txt(88, 780, "B  波数的空间含义：同一发生环上的不同 Fourier 模态", size=24, weight=700))

    bx, bw = 155.0, 985.0
    rows = [(2, 855.0, ORANGE), (3, 965.0, GREEN), (6, 1075.0, BLUE)]

    def cell_x(cell):
        return bx + cell / N * bw

    for m, baseline, color in rows:
        q_m = 2.0 * pi * m / N
        lam_m = dispersion(q_m)
        ell_m = N / m
        status = "增长" if lam_m > 0 else "衰减"
        s.append(line(bx, baseline, bx + bw, baseline, stroke=LIGHT_GRID, width=1.5))
        pts = []
        for k in range(481):
            cell = N * k / 480
            value = cos(q_m * cell)
            pts.append((cell_x(cell), baseline - 34 * value))
        s.append(path(pts, stroke=color, width=3.2, fill="none"))
        s.append(txt(1180, baseline + 7, f"m={m}，ℓ={ell_m:.0f}细胞，λ={lam_m:.3f}（{status}）", size=18, fill=color, weight=600))

    # Mark the three peaks and one wavelength for m=3.
    for cell in [0, 8, 16, 24]:
        s.append(f'<circle cx="{cell_x(cell):.2f}" cy="{965-34:.2f}" r="6.5" fill="{GREEN}" stroke="white" stroke-width="2"/>')
    bracket_y = 915
    x0, x8 = cell_x(0), cell_x(8)
    s.append(line(x0, bracket_y, x8, bracket_y, stroke=GREEN, width=2))
    s.append(line(x0, bracket_y - 8, x0, bracket_y + 8, stroke=GREEN, width=2))
    s.append(line(x8, bracket_y - 8, x8, bracket_y + 8, stroke=GREEN, width=2))
    s.append(txt((x0 + x8) / 2, bracket_y - 10, "一个波长 ℓ=8 个细胞", size=16, fill=GREEN, anchor="middle", weight=600))
    s.append(txt(cell_x(20), 914, "m=3 → 一圈3个候选峰", size=17, fill=GREEN, anchor="middle", weight=700))

    for cell in range(0, N + 1, 4):
        xx = cell_x(cell)
        s.append(line(xx, 1115, xx, 1123, stroke=GRAY, width=1.5))
        s.append(txt(xx, 1147, str(cell), size=16, fill=GRAY, anchor="middle"))
    s.append(line(bx, 1115, bx + bw, 1115, stroke=GRAY, width=2))
    s.append(txt(bx + bw / 2, 1160, "发生环上的细胞编号", size=19, anchor="middle", weight=600))

    s.append(txt(WIDTH / 2, 1215, "读图：q* 决定早期最易放大的峰间距；Apeak 是否达到 Aon 仍由初始扰动、非线性饱和及原基事件决定。", size=18, fill=GRAY, anchor="middle"))
    s.append('</svg>')
    return "\n".join(s)


def main():
    svg = make_svg()
    svg_path = OUT_DIR / "fig_dispersion_auxin.svg"
    html_path = OUT_DIR / "fig_dispersion_auxin.html"
    svg_path.write_text(svg, encoding="utf-8")
    html_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<style>@page{size:1480px 1250px;margin:0}html,body{margin:0;width:1480px;height:1250px;overflow:hidden;background:#FAFBFC}</style>"
        f"</head><body>{svg}</body></html>",
        encoding="utf-8",
    )
    print(f"Saved {svg_path}")
    print(f"Saved {html_path}")


if __name__ == "__main__":
    main()
