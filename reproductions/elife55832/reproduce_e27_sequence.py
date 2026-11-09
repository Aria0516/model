#!/usr/bin/env python3
"""Minimal image-level reproduction for eLife 55832 using E27/SAM7.

This is intentionally separate from the legacy sam_spaghetti environment.  It
uses the authors' preprocessed, organ-cropped TIFF stacks and only NumPy/Pillow
to test the Figure 1 idea that temporal progression approximately corresponds
to angular rotation of the auxin pattern.

It is not a replacement for nuclear detection, nonlinear registration, L1
surface extraction, population averaging, or manual primordium correction in
the paper's full pipeline.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


FILES = {
    0: ("qDII-CLV3-DR5-E27-LD-SAM7-No-organs.tif", 377_620_885),
    5: ("qDII-CLV3-DR5-E27-LD-SAM7-T5-No-organs.tif", 377_622_023),
    10: ("qDII-CLV3-DR5-E27-LD-SAM7-T10-No-organs.tif", 377_622_355),
}
CHANNEL_NAMES = ["DIIV", "DR5", "TagBFP", "CLV3"]


def parse_imagej_description(description: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in description.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def max_project_channels(path: Path) -> tuple[dict[str, np.ndarray], float, dict[str, str]]:
    with Image.open(path) as image:
        description = str(image.tag_v2.get(270, ""))
        metadata = parse_imagej_description(description)
        n_channels = int(metadata.get("channels", "4"))
        n_slices = int(metadata.get("slices", "1"))
        n_images = int(metadata.get("images", str(n_channels * n_slices)))
        if n_channels != 4 or n_images != n_channels * n_slices:
            raise ValueError(f"Unexpected hyperstack metadata in {path.name}: {metadata}")
        if image.n_frames != n_images:
            raise ValueError(f"Expected {n_images} TIFF pages, found {image.n_frames} in {path.name}")

        x_resolution = float(image.tag_v2.get(282, 1.0))
        pixel_um = 1.0 / x_resolution
        projections = [np.zeros((image.height, image.width), dtype=np.uint16) for _ in range(n_channels)]
        for page in range(n_images):
            image.seek(page)
            channel = page % n_channels
            frame = np.asarray(image, dtype=np.uint16)
            np.maximum(projections[channel], frame, out=projections[channel])
    return dict(zip(CHANNEL_NAMES, projections)), pixel_um, metadata


def positive_percentile(values: np.ndarray, percentile: float) -> float:
    positive = values[values > 0]
    if not len(positive):
        return 0.0
    return float(np.percentile(positive, percentile))


def robust_unit(image: np.ndarray, low: float = 1.0, high: float = 99.7) -> np.ndarray:
    image = image.astype(np.float64, copy=False)
    lo = positive_percentile(image, low)
    hi = positive_percentile(image, high)
    if hi <= lo:
        return np.zeros_like(image)
    return np.clip((image - lo) / (hi - lo), 0.0, 1.0)


def weighted_center(clv3: np.ndarray) -> tuple[float, float]:
    scaled = robust_unit(clv3, 5.0, 99.8)
    threshold = float(np.percentile(scaled[scaled > 0], 92.0)) if np.any(scaled > 0) else 0.5
    weight = np.clip(scaled - threshold, 0.0, None) ** 2
    yy, xx = np.indices(weight.shape)
    total = float(weight.sum())
    if total <= 0:
        return (clv3.shape[1] / 2.0, clv3.shape[0] / 2.0)  # pragma: no cover
    return float((xx * weight).sum() / total), float((yy * weight).sum() / total)


def block_sum(image: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return image.astype(np.float64, copy=True)
    k = 2 * radius + 1
    padded = np.pad(image.astype(np.float64), ((radius, radius), (radius, radius)), mode="constant")
    integral = np.pad(padded, ((1, 0), (1, 0)), mode="constant").cumsum(0).cumsum(1)
    return integral[k:, k:] - integral[:-k, k:] - integral[k:, :-k] + integral[:-k, :-k]


def auxin_proxy(projections: dict[str, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    dii = projections["DIIV"].astype(np.float64)
    reference = projections["TagBFP"].astype(np.float64)
    dii -= positive_percentile(dii, 1.0)
    reference -= positive_percentile(reference, 1.0)
    np.maximum(dii, 0.0, out=dii)
    np.maximum(reference, 0.0, out=reference)
    ref_threshold = positive_percentile(reference, 68.0)
    mask = reference > ref_threshold
    stabilizer = max(1.0, positive_percentile(reference, 50.0) * 0.03)
    ratio = dii / (reference + stabilizer)
    valid = ratio[mask & np.isfinite(ratio)]
    if not len(valid):
        raise ValueError("No valid qDII pixels after reference masking")
    lo, hi = np.percentile(valid, [3.0, 97.0])
    qdii = np.clip((ratio - lo) / max(hi - lo, 1e-12), 0.0, 1.0)
    auxin = 1.0 - qdii
    smooth_num = block_sum(auxin * mask, 6)
    smooth_den = block_sum(mask.astype(np.float64), 6)
    smooth = np.divide(smooth_num, smooth_den, out=np.full_like(smooth_num, np.nan), where=smooth_den >= 3.0)
    return smooth, smooth_den >= 3.0


def detect_projected_nuclei(reference: np.ndarray, pixel_um: float) -> tuple[np.ndarray, np.ndarray]:
    """Approximate one 2D point per bright projected TagBFP nucleus.

    The paper detects nuclei in 3D scale space.  This deliberately smaller
    check uses local maxima and physical-distance non-maximum suppression on a
    maximum projection; the distinction is reported in the output metadata.
    """
    scaled = robust_unit(reference, 1.0, 99.8)
    smoothed = block_sum(scaled, 2) / 25.0
    positive = smoothed[smoothed > 0]
    threshold = float(np.percentile(positive, 72.0))
    local = smoothed >= threshold
    for dy, dx in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
        shifted = np.full_like(smoothed, -np.inf)
        y_src = slice(max(0, -dy), min(smoothed.shape[0], smoothed.shape[0] - dy))
        x_src = slice(max(0, -dx), min(smoothed.shape[1], smoothed.shape[1] - dx))
        y_dst = slice(max(0, dy), min(smoothed.shape[0], smoothed.shape[0] + dy))
        x_dst = slice(max(0, dx), min(smoothed.shape[1], smoothed.shape[1] + dx))
        shifted[y_dst, x_dst] = smoothed[y_src, x_src]
        local &= smoothed >= shifted

    yy, xx = np.nonzero(local)
    order = np.argsort(smoothed[yy, xx])[::-1]
    min_distance = max(4, int(round(1.8 / pixel_um)))
    suppressed = np.zeros(smoothed.shape, dtype=bool)
    keep_x: list[int] = []
    keep_y: list[int] = []
    for index in order:
        y, x = int(yy[index]), int(xx[index])
        if suppressed[y, x]:
            continue
        keep_x.append(x)
        keep_y.append(y)
        y0, y1 = max(0, y - min_distance), min(smoothed.shape[0], y + min_distance + 1)
        x0, x1 = max(0, x - min_distance), min(smoothed.shape[1], x + min_distance + 1)
        y_grid, x_grid = np.ogrid[y0:y1, x0:x1]
        disk = (x_grid - x) ** 2 + (y_grid - y) ** 2 <= min_distance ** 2
        suppressed[y0:y1, x0:x1][disk] = True
        if len(keep_x) >= 2500:
            break
    return np.asarray(keep_x, dtype=np.int64), np.asarray(keep_y, dtype=np.int64)


def quantify_projected_nuclei(
    projections: dict[str, np.ndarray], pixel_um: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[float, float]]:
    x_px, y_px = detect_projected_nuclei(projections["TagBFP"], pixel_um)
    if len(x_px) < 100:
        raise ValueError(f"Only {len(x_px)} projected nuclei detected")

    local_signals: dict[str, np.ndarray] = {}
    for name, image in projections.items():
        local_signals[name] = block_sum(image.astype(np.float64), 2)[y_px, x_px] / 25.0

    reference = local_signals["TagBFP"]
    dii = local_signals["DIIV"]
    valid_reference = reference > np.percentile(reference, 20.0)
    ratio = dii / np.maximum(reference, 1.0)
    lo, hi = np.percentile(ratio[valid_reference], [3.0, 97.0])
    auxin = 1.0 - np.clip((ratio - lo) / max(hi - lo, 1e-12), 0.0, 1.0)

    clv3 = local_signals["CLV3"]
    clv3_threshold = np.percentile(clv3, 91.0)
    center_weight = np.clip(clv3 - clv3_threshold, 0.0, None) ** 2
    if center_weight.sum() <= 0:
        center = (float(np.median(x_px)), float(np.median(y_px)))
    else:
        center = (float(np.average(x_px, weights=center_weight)), float(np.average(y_px, weights=center_weight)))
    return x_px, y_px, auxin, center


def continuous_polar_map(
    x_px: np.ndarray,
    y_px: np.ndarray,
    values: np.ndarray,
    center: tuple[float, float],
    pixel_um: float,
    radial_edges_um: np.ndarray,
    angle_edges_deg: np.ndarray,
    cell_radius_um: float = 7.5,
    density_k_per_um: float = 0.55,
) -> tuple[np.ndarray, np.ndarray]:
    """Continuous field using the sigmoid kernel reported in Appendix 3."""
    radial_centers = (radial_edges_um[:-1] + radial_edges_um[1:]) / 2.0
    angle_centers = (angle_edges_deg[:-1] + angle_edges_deg[1:]) / 2.0
    rr, aa = np.meshgrid(radial_centers, np.radians(angle_centers), indexing="ij")
    gx = (rr * np.cos(aa)).ravel()
    gy = (rr * np.sin(aa)).ravel()
    nx = (x_px - center[0]) * pixel_um
    ny = -(y_px - center[1]) * pixel_um

    field = np.empty_like(gx)
    confidence = np.empty_like(gx)
    for start in range(0, len(gx), 700):
        stop = min(len(gx), start + 700)
        distance = np.hypot(gx[start:stop, None] - nx[None, :], gy[start:stop, None] - ny[None, :])
        weights = 0.5 - 0.5 * np.tanh(density_k_per_um * (distance - cell_radius_um))
        denominator = weights.sum(axis=1)
        field[start:stop] = np.divide(weights @ values, denominator, out=np.full(stop-start, np.nan), where=denominator > 0.25)
        confidence[start:stop] = denominator
    return field.reshape(rr.shape), confidence.reshape(rr.shape)


def polar_map(
    image: np.ndarray,
    valid: np.ndarray,
    center: tuple[float, float],
    pixel_um: float,
    radial_edges_um: np.ndarray,
    angle_edges_deg: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    yy, xx = np.indices(image.shape)
    dx = (xx - center[0]) * pixel_um
    dy = -(yy - center[1]) * pixel_um
    radius = np.hypot(dx, dy)
    angle = (np.degrees(np.arctan2(dy, dx)) + 360.0) % 360.0
    r_bin = np.digitize(radius.ravel(), radial_edges_um) - 1
    a_bin = np.digitize(angle.ravel(), angle_edges_deg) - 1
    values = image.ravel()
    keep = valid.ravel() & np.isfinite(values) & (r_bin >= 0) & (r_bin < len(radial_edges_um) - 1) & (a_bin >= 0) & (a_bin < len(angle_edges_deg) - 1)
    flat = r_bin[keep] * (len(angle_edges_deg) - 1) + a_bin[keep]
    sums = np.bincount(flat, weights=values[keep], minlength=(len(radial_edges_um) - 1) * (len(angle_edges_deg) - 1))
    counts = np.bincount(flat, minlength=len(sums))
    result = np.divide(sums, counts, out=np.full(len(sums), np.nan), where=counts > 0)
    return result.reshape(len(radial_edges_um) - 1, len(angle_edges_deg) - 1), counts.reshape(len(radial_edges_um) - 1, len(angle_edges_deg) - 1)


def correlation(a: np.ndarray, b: np.ndarray) -> float:
    valid = np.isfinite(a) & np.isfinite(b)
    if valid.sum() < 20:
        return float("nan")
    av, bv = a[valid], b[valid]
    av = av - av.mean()
    bv = bv - bv.mean()
    denom = float(np.sqrt(np.sum(av * av) * np.sum(bv * bv)))
    return float(np.sum(av * bv) / denom) if denom else float("nan")


def rotation_curve(reference: np.ndarray, target: np.ndarray, step_deg: float) -> tuple[np.ndarray, np.ndarray]:
    shifts = np.arange(-180.0, 180.0, step_deg)
    correlations = np.array([correlation(np.roll(reference, int(round(shift / step_deg)), axis=1), target) for shift in shifts])
    return shifts, correlations


def yellow_image(values: np.ndarray, valid: np.ndarray, center: tuple[float, float]) -> Image.Image:
    scaled = np.nan_to_num(values, nan=0.0)
    rgb = np.zeros((*scaled.shape, 3), dtype=np.uint8)
    rgb[..., 0] = np.round(255 * scaled).astype(np.uint8)
    rgb[..., 1] = np.round(225 * scaled).astype(np.uint8)
    rgb[~valid] //= 5
    image = Image.fromarray(rgb).resize((512, 512), Image.Resampling.BILINEAR)
    draw = ImageDraw.Draw(image)
    sx, sy = 512 / values.shape[1], 512 / values.shape[0]
    x, y = center[0] * sx, center[1] * sy
    draw.ellipse((x - 5, y - 5, x + 5, y + 5), outline=(255, 0, 255), width=2)
    return image


def write_rotation_svg(path: Path, curves: dict[int, tuple[np.ndarray, np.ndarray]], best: dict[int, float]) -> None:
    width, height = 900, 540
    left, top, plot_w, plot_h = 85, 55, 750, 400
    all_corr = np.concatenate([c for _, c in curves.values()])
    finite = all_corr[np.isfinite(all_corr)]
    y_min, y_max = float(finite.min()), float(finite.max())
    if y_max - y_min < 1e-8:
        y_max = y_min + 1.0
    colors = {5: "#2a9d8f", 10: "#e76f51"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.title{font-size:20px;font-weight:700}.axis{font-size:14px}.small{font-size:12px}</style>',
        '<text x="85" y="30" class="title">E27/SAM7 auxin-proxy rotational similarity</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#222"/>',
    ]
    for time, (shifts, corr) in curves.items():
        coords = []
        for xval, yval in zip(shifts, corr):
            if np.isfinite(yval):
                x = left + (xval + 180.0) / 360.0 * plot_w
                y = top + (y_max - yval) / (y_max - y_min) * plot_h
                coords.append(f"{x:.2f},{y:.2f}")
        parts.append(f'<polyline points="{" ".join(coords)}" fill="none" stroke="{colors[time]}" stroke-width="2"/>')
        parts.append(f'<text x="{left+15}" y="{top+25+22*(time//5-1)}" fill="{colors[time]}" class="small">T0 vs T{time}: best {best[time]:.1f} deg</text>')
    for val in [-180, -90, 0, 90, 180]:
        x = left + (val + 180.0) / 360.0 * plot_w
        parts += [f'<line x1="{x}" y1="{top+plot_h}" x2="{x}" y2="{top+plot_h+6}" stroke="#222"/>', f'<text x="{x}" y="{top+plot_h+23}" text-anchor="middle" class="small">{val}</text>']
    for frac in np.linspace(0, 1, 5):
        value = y_min + frac * (y_max - y_min)
        y = top + (1-frac) * plot_h
        parts += [f'<line x1="{left-6}" y1="{y}" x2="{left}" y2="{y}" stroke="#222"/>', f'<text x="{left-10}" y="{y+4}" text-anchor="end" class="small">{value:.2f}</text>']
    xgold = left + (137.5 + 180.0) / 360.0 * plot_w
    xgold_negative = left + (-137.5 + 180.0) / 360.0 * plot_w
    parts += [
        f'<line x1="{xgold}" y1="{top}" x2="{xgold}" y2="{top+plot_h}" stroke="#777" stroke-dasharray="6,5"/>',
        f'<line x1="{xgold_negative}" y1="{top}" x2="{xgold_negative}" y2="{top+plot_h}" stroke="#777" stroke-dasharray="6,5"/>',
        f'<text x="{xgold+5}" y="{top+plot_h-10}" class="small">+137.5 deg</text>',
        f'<text x="{xgold_negative+5}" y="{top+plot_h-10}" class="small">-137.5 deg</text>',
        f'<text x="{left+plot_w/2}" y="510" text-anchor="middle" class="axis">rotation applied to T0 auxin proxy (degrees)</text>',
        f'<text x="22" y="{top+plot_h/2}" text-anchor="middle" class="axis" transform="rotate(-90 22 {top+plot_h/2})">Pearson correlation</text>',
        '</svg>',
    ]
    path.write_text("\n".join(parts), encoding="utf-8")


def write_rotation_png(path: Path, curves: dict[int, tuple[np.ndarray, np.ndarray]], best: dict[int, float]) -> None:
    width, height = 900, 540
    left, top, plot_w, plot_h = 85, 55, 750, 400
    all_corr = np.concatenate([c for _, c in curves.values()])
    finite = all_corr[np.isfinite(all_corr)]
    y_min, y_max = float(finite.min()), float(finite.max())
    if y_max - y_min < 1e-8:
        y_max = y_min + 1.0
    colors = {5: (42, 157, 143), 10: (231, 111, 81)}
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((left, 20), "E27/SAM7 auxin-proxy rotational similarity", fill="black")
    draw.rectangle((left, top, left + plot_w, top + plot_h), outline=(34, 34, 34), width=1)
    for time, (shifts, corr) in curves.items():
        points = []
        for xval, yval in zip(shifts, corr):
            if np.isfinite(yval):
                x = left + (xval + 180.0) / 360.0 * plot_w
                y = top + (y_max - yval) / (y_max - y_min) * plot_h
                points.append((x, y))
        draw.line(points, fill=colors[time], width=3)
        draw.text((left + 15, top + 12 + 20 * (time // 5 - 1)), f"T0 vs T{time}: best {best[time]:.1f} deg", fill=colors[time])
    for val in [-180, -90, 0, 90, 180]:
        x = left + (val + 180.0) / 360.0 * plot_w
        draw.line((x, top + plot_h, x, top + plot_h + 6), fill="black")
        draw.text((x - 14, top + plot_h + 10), str(val), fill="black")
    for frac in np.linspace(0, 1, 5):
        value = y_min + frac * (y_max - y_min)
        y = top + (1.0 - frac) * plot_h
        draw.line((left - 6, y, left, y), fill="black")
        draw.text((30, y - 6), f"{value:.2f}", fill="black")
    for golden_angle in [-137.5, 137.5]:
        xgold = left + (golden_angle + 180.0) / 360.0 * plot_w
        for y in range(top, top + plot_h, 12):
            draw.line((xgold, y, xgold, min(y + 6, top + plot_h)), fill=(110, 110, 110), width=1)
        draw.text((xgold + 5, top + plot_h - 18), f"{golden_angle:+.1f} deg", fill=(80, 80, 80))
    draw.text((left + plot_w // 2 - 95, 505), "rotation applied to T0 (degrees)", fill="black")
    image.save(path)


def validate_files(data_dir: Path) -> list[tuple[int, Path]]:
    result = []
    problems = []
    for time, (name, expected_size) in FILES.items():
        path = data_dir / name
        if not path.exists():
            problems.append(f"missing {name}")
        elif path.stat().st_size != expected_size:
            problems.append(f"incomplete {name}: {path.stat().st_size} bytes, expected {expected_size}")
        else:
            result.append((time, path))
    if problems:
        raise SystemExit("Input validation failed:\n- " + "\n- ".join(problems))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/E27_SAM7"))
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    files = validate_files(args.data)
    args.output.mkdir(parents=True, exist_ok=True)

    radial_edges = np.arange(18.0, 96.0 + 2.0, 2.0)
    angle_edges = np.arange(0.0, 360.0 + 2.0, 2.0)
    maps: dict[int, np.ndarray] = {}
    panels: dict[int, Image.Image] = {}
    metadata_summary: dict[int, dict[str, object]] = {}
    for time, path in files:
        projections, pixel_um, metadata = max_project_channels(path)
        auxin, valid = auxin_proxy(projections)
        x_px, y_px, nucleus_auxin, center = quantify_projected_nuclei(projections, pixel_um)
        maps[time], confidence = continuous_polar_map(
            x_px, y_px, nucleus_auxin, center, pixel_um, radial_edges, angle_edges
        )
        panels[time] = yellow_image(auxin, valid, center)
        metadata_summary[time] = {
            "file": path.name,
            "bytes": path.stat().st_size,
            "pixel_um": pixel_um,
            "center_xy_pixels": center,
            "imagej": metadata,
            "projected_nuclei": int(len(x_px)),
            "valid_polar_bins": int(np.isfinite(maps[time]).sum()),
            "continuous_map_kernel": {"radius_um": 7.5, "density_k_per_um": 0.55},
        }

    sheet = Image.new("RGB", (512 * 3, 560), "white")
    draw = ImageDraw.Draw(sheet)
    for column, time in enumerate([0, 5, 10]):
        sheet.paste(panels[time], (512 * column, 40))
        draw.text((512 * column + 12, 12), f"E27/SAM7  t={time} h  auxin proxy", fill="black")
    sheet.save(args.output / "e27_sam7_auxin_proxy.png")

    curves: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    best: dict[int, float] = {}
    best_correlation: dict[int, float] = {}
    best_phyllotactic: dict[int, float] = {}
    best_phyllotactic_correlation: dict[int, float] = {}
    golden_correlations: dict[int, dict[str, float]] = {}
    step = float(angle_edges[1] - angle_edges[0])
    for time in [5, 10]:
        shifts, corr = rotation_curve(maps[0], maps[time], step)
        curves[time] = (shifts, corr)
        index = int(np.nanargmax(corr))
        best[time] = float(shifts[index])
        best_correlation[time] = float(corr[index])
        phyllotactic_region = np.abs(shifts) >= 90.0
        phyllotactic_indices = np.flatnonzero(phyllotactic_region)
        p_index = int(phyllotactic_indices[np.nanargmax(corr[phyllotactic_region])])
        best_phyllotactic[time] = float(shifts[p_index])
        best_phyllotactic_correlation[time] = float(corr[p_index])
        plus_index = int(np.argmin(np.abs(shifts - 137.5)))
        minus_index = int(np.argmin(np.abs(shifts + 137.5)))
        golden_correlations[time] = {
            "+137.5_deg": float(corr[plus_index]),
            "-137.5_deg": float(corr[minus_index]),
        }

    with (args.output / "e27_sam7_rotation_curve.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rotation_deg", "corr_t0_t5", "corr_t0_t10"])
        for i, shift in enumerate(curves[5][0]):
            writer.writerow([f"{shift:.1f}", f"{curves[5][1][i]:.8f}", f"{curves[10][1][i]:.8f}"])
    write_rotation_svg(args.output / "e27_sam7_rotation_curve.svg", curves, best)
    write_rotation_png(args.output / "e27_sam7_rotation_curve.png", curves, best)

    summary = {
        "paper": "Galvan-Ampudia et al., eLife 2020, e55832",
        "scope": "single-sequence projected-nucleus proxy check; not the full population/3D-nucleus pipeline",
        "channel_order": CHANNEL_NAMES,
        "radial_analysis_um": [float(radial_edges[0]), float(radial_edges[-1])],
        "angle_bin_deg": step,
        "best_rotation_deg": {str(k): v for k, v in best.items()},
        "best_correlation": {str(k): v for k, v in best_correlation.items()},
        "best_rotation_abs_ge_90_deg": {str(k): v for k, v in best_phyllotactic.items()},
        "best_correlation_abs_ge_90_deg": {str(k): v for k, v in best_phyllotactic_correlation.items()},
        "correlation_at_paper_divergence_angle": {str(k): v for k, v in golden_correlations.items()},
        "paper_reference": {"divergence_angle_deg": 137.5, "plastochron_h": "12 +/- 2"},
        "metadata": {str(k): v for k, v in metadata_summary.items()},
    }
    (args.output / "e27_sam7_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
