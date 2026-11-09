"""Create stage sheet, GIF, and auxin-range SVG for the GFtbox time series."""

from __future__ import annotations

import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs_timeseries"
FRAME_FILES = [
    ("t=0.5", OUT / "jonsson_gftbox_t00p5.png"),
    ("t=1", OUT / "jonsson_gftbox_t01p0.png"),
    ("t=2", OUT / "jonsson_gftbox_t02p0.png"),
    ("t=4", OUT / "jonsson_gftbox_t04p0.png"),
    ("t=6", OUT / "jonsson_gftbox_t06p0.png"),
    ("t=8", OUT / "jonsson_gftbox_t08p0.png"),
]


def fit_image(img: Image.Image, size: tuple[int, int]) -> Image.Image:
    copy = img.copy()
    copy.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    x = (size[0] - copy.width) // 2
    y = (size[1] - copy.height) // 2
    canvas.paste(copy, (x, y))
    return canvas


def make_sheet() -> Path:
    font = ImageFont.load_default()
    tile = (560, 470)
    label_h = 34
    cols = 3
    rows = 2
    margin = 28
    sheet = Image.new(
        "RGB",
        (cols * tile[0] + (cols + 1) * margin, rows * (tile[1] + label_h) + (rows + 1) * margin),
        "white",
    )
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 8), "Jonsson auxin-PIN dynamics embedded in GFtbox 3D mesh", fill=(20, 20, 20), font=font)
    for idx, (label, path) in enumerate(FRAME_FILES):
        img = Image.open(path).convert("RGB")
        thumb = fit_image(img, tile)
        c = idx % cols
        r = idx // cols
        x = margin + c * (tile[0] + margin)
        y = margin + r * (tile[1] + label_h + margin)
        draw.rectangle((x - 1, y + label_h - 1, x + tile[0] + 1, y + label_h + tile[1] + 1), outline=(180, 180, 180))
        draw.text((x, y), label, fill=(20, 20, 20), font=font)
        sheet.paste(thumb, (x, y + label_h))
    out = OUT / "jonsson_gftbox_timeseries_sheet.png"
    sheet.save(out)
    return out


def make_gif() -> Path:
    frames = []
    for label, path in FRAME_FILES:
        img = Image.open(path).convert("RGB")
        frame = fit_image(img, (980, 790))
        draw = ImageDraw.Draw(frame)
        draw.rectangle((0, 0, 170, 42), fill=(255, 255, 255))
        draw.text((18, 14), label, fill=(20, 20, 20), font=ImageFont.load_default())
        frames.append(frame)
    out = OUT / "jonsson_gftbox_timeseries.gif"
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=850, loop=0, optimize=True)
    return out


def make_auxin_svg() -> Path:
    rows = []
    with (OUT / "timeseries_summary.csv").open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append({k: float(v) for k, v in row.items()})

    w, h = 840, 360
    ml, mr, mt, mb = 72, 28, 36, 56
    xs = [r["time"] for r in rows]
    ymin = min(r["auxin_min"] for r in rows)
    ymax = max(r["auxin_max"] for r in rows)
    ypad = 0.03
    ymin -= ypad
    ymax += ypad

    def xmap(x: float) -> float:
        return ml + (x - min(xs)) / (max(xs) - min(xs)) * (w - ml - mr)

    def ymap(y: float) -> float:
        return mt + (ymax - y) / (ymax - ymin) * (h - mt - mb)

    max_pts = " ".join(f"{xmap(r['time']):.1f},{ymap(r['auxin_max']):.1f}" for r in rows)
    min_pts = " ".join(f"{xmap(r['time']):.1f},{ymap(r['auxin_min']):.1f}" for r in rows)
    band = max_pts + " " + " ".join(f"{xmap(r['time']):.1f},{ymap(r['auxin_min']):.1f}" for r in reversed(rows))
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.axis{stroke:#333;stroke-width:1}.grid{stroke:#ddd;stroke-width:1}</style>',
        '<text x="24" y="24" font-size="18" font-weight="700">Auxin range over GFtbox time</text>',
        f'<polygon points="{band}" fill="#f4b6a8" opacity="0.45"/>',
        f'<polyline points="{max_pts}" fill="none" stroke="#b2182b" stroke-width="3"/>',
        f'<polyline points="{min_pts}" fill="none" stroke="#2166ac" stroke-width="3"/>',
        f'<line class="axis" x1="{ml}" y1="{h-mb}" x2="{w-mr}" y2="{h-mb}"/>',
        f'<line class="axis" x1="{ml}" y1="{mt}" x2="{ml}" y2="{h-mb}"/>',
        '<text x="718" y="63" font-size="12" fill="#b2182b">max auxin</text>',
        '<text x="718" y="83" font-size="12" fill="#2166ac">min auxin</text>',
    ]
    for r in rows:
        x = xmap(r["time"])
        lines.append(f'<line class="grid" x1="{x:.1f}" y1="{mt}" x2="{x:.1f}" y2="{h-mb}"/>')
        lines.append(f'<text x="{x-10:.1f}" y="{h-mb+24}" font-size="11">{r["time"]:g}</text>')
    for y in [0.9, 1.0, 1.1, 1.2]:
        yy = ymap(y)
        lines.append(f'<line class="grid" x1="{ml}" y1="{yy:.1f}" x2="{w-mr}" y2="{yy:.1f}"/>')
        lines.append(f'<text x="30" y="{yy+4:.1f}" font-size="11">{y:.1f}</text>')
    lines.append(f'<text x="{w/2-20:.1f}" y="{h-14}" font-size="12">GFtbox time</text>')
    lines.append('<text x="8" y="178" font-size="12" transform="rotate(-90 8,178)">auxin</text>')
    lines.append("</svg>")
    out = OUT / "jonsson_gftbox_auxin_range.svg"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    for _, p in FRAME_FILES:
        if not p.exists():
            raise FileNotFoundError(p)
    print("sheet", make_sheet())
    print("gif", make_gif())
    print("svg", make_auxin_svg())
