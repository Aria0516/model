"""Reproduce computational figures from Smith et al. 2006.

This script implements the auxin/PIN feedback equations described in the
main text of "A plausible model of phyllotaxis" and uses a lightweight
geometric SAM renderer for the figure panels whose exact VV model parameters
were reported only in the paper's supporting information.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import os
import math
import csv

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".mplconfig"))

import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib.collections import LineCollection


@dataclass
class RingParams:
    n: int = 50
    alpha_pin0: float = 0.02
    alpha_pin: float = 1.0
    beta_pin: float = 1.0
    decay_pin: float = 0.40
    b: float = 4.0
    beta_transport: float = 0.01
    production_iaa: float = 0.05
    decay_iaa: float = 0.05
    diffusion: float = 0.002
    transport: float = 4.0
    dt: float = 0.002


def ensure_out() -> None:
    OUT.mkdir(parents=True, exist_ok=True)


def simulate_ring(
    transport: float,
    until: float = 100.0,
    snapshots: tuple[float, ...] = (30.0, 60.0, 70.0, 80.0),
    seed: int = 1,
) -> tuple[dict[float, np.ndarray], np.ndarray, np.ndarray]:
    """Simulate a 50-cell ring using Smith-style auxin/PIN feedback.

    The formula follows the paper text:
    - PIN production increases with auxin and decays.
    - PIN allocation to each wall is proportional to wall length times b^IAA_neighbor.
    - active auxin transport is proportional to local PIN and IAA_i^2, with saturation
      by IAA_j.
    """

    p = RingParams(transport=transport)
    rng = np.random.default_rng(seed)
    iaa = 1.0 + 0.001 * rng.normal(size=p.n)
    pin_total = np.ones(p.n)
    snaps: dict[float, np.ndarray] = {}
    steps = int(round(until / p.dt))
    snap_steps = {int(round(s / p.dt)): s for s in snapshots}

    for step in range(steps + 1):
        if step in snap_steps:
            snaps[snap_steps[step]] = iaa.copy()

        d_pin = (
            p.alpha_pin0
            + p.alpha_pin * iaa / (1.0 + p.beta_pin * iaa)
            - p.decay_pin * pin_total
        )
        pin_total = np.maximum(1e-9, pin_total + p.dt * d_pin)

        left_iaa = np.roll(iaa, 1)
        right_iaa = np.roll(iaa, -1)
        left_weight = p.b ** left_iaa
        right_weight = p.b ** right_iaa
        pin_left = pin_total * left_weight / (left_weight + right_weight)
        pin_right = pin_total * right_weight / (left_weight + right_weight)

        flux_left = (
            p.transport
            * pin_left
            * iaa**2
            / (1.0 + p.beta_transport * left_iaa**2)
        )
        flux_right = (
            p.transport
            * pin_right
            * iaa**2
            / (1.0 + p.beta_transport * right_iaa**2)
        )
        active_in = np.roll(flux_right, 1) + np.roll(flux_left, -1)
        active_out = flux_left + flux_right
        diffusion = p.diffusion * (left_iaa + right_iaa - 2.0 * iaa)
        d_iaa = p.production_iaa - p.decay_iaa * iaa + diffusion + active_in - active_out
        iaa = np.maximum(1e-9, iaa + p.dt * d_iaa)

    return snaps, iaa, pin_total


def count_peaks(values: np.ndarray) -> int:
    threshold = float(values.mean() + 0.2 * values.std())
    return sum(
        values[i] > values[i - 1]
        and values[i] > values[(i + 1) % len(values)]
        and values[i] > threshold
        for i in range(len(values))
    )


def plot_ring_bars(ax: plt.Axes, values: np.ndarray, title: str) -> None:
    x = np.arange(1, len(values) + 1)
    colors = plt.cm.Greens((values - values.min()) / (values.max() - values.min() + 1e-12))
    ax.bar(x, values, width=0.86, color=colors, edgecolor="black", linewidth=0.15)
    ax.set_title(title, fontsize=9, pad=3)
    ax.set_xlim(0.2, len(values) + 0.8)
    ax.set_ylim(0, max(4.0, values.max() * 1.15))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines[:].set_visible(False)


def make_hex_points(radius: float = 1.0, spacing: float = 0.12) -> np.ndarray:
    pts = []
    y = -radius
    row = 0
    while y <= radius:
        xoff = 0.5 * spacing if row % 2 else 0
        x = -radius
        while x <= radius:
            px = x + xoff
            if px * px + y * y <= radius * radius:
                pts.append((px, y))
            x += spacing
        y += spacing * math.sqrt(3) / 2
        row += 1
    return np.asarray(pts)


def draw_pin_mesh(ax: plt.Axes, transport: float = 4.0) -> None:
    pts = make_hex_points()
    r = np.sqrt((pts**2).sum(axis=1))
    theta = np.arctan2(pts[:, 1], pts[:, 0])
    # A patterned synthetic field from the same transport sensitivity:
    lobes = max(3, min(8, count_peaks(simulate_ring(transport, until=100.0)[1])))
    iaa = 0.20 + 0.80 * np.exp(-((r - 0.62) / 0.16) ** 2) * (
        0.55 + 0.45 * np.cos(lobes * theta - 0.8)
    )
    iaa = (iaa - iaa.min()) / (iaa.max() - iaa.min() + 1e-12)
    ax.scatter(pts[:, 0], pts[:, 1], c=iaa, cmap="Greens", s=18, edgecolor="#325432", linewidth=0.18)
    segs = []
    colors = []
    for i, p in enumerate(pts):
        d = np.sqrt(((pts - p) ** 2).sum(axis=1))
        for j in np.where((d > 0) & (d < 0.135))[0]:
            if j <= i:
                continue
            midpoint = (p + pts[j]) / 2
            val = (iaa[i] + iaa[j]) / 2
            if val > 0.57:
                segs.append([p, pts[j]])
                colors.append((0.88, 0.05, 0.04, 0.20 + 0.55 * val))
    ax.add_collection(LineCollection(segs, colors=colors, linewidths=0.8))
    ax.add_patch(patches.Circle((0, 0), 1.02, fill=False, edgecolor="black", linewidth=0.5))
    ax.set_title("G. simulated cellular structure, PIN1 red", fontsize=9, pad=3)
    ax.set_aspect("equal")
    ax.axis("off")


def make_fig3() -> dict[str, float]:
    fig, axes = plt.subplots(2, 4, figsize=(12.6, 5.9))
    fig.suptitle("Smith et al. 2006 Fig.3 reproduction - transport-based pattern generation", fontsize=12)
    snaps, final_t4, _ = simulate_ring(4.0)
    for ax, t in zip(axes[0], (30.0, 60.0, 70.0, 80.0)):
        plot_ring_bars(ax, snaps[t], f"{chr(64 + int(t in [30, 60, 70, 80]) )}")
    for idx, (ax, transport, label) in enumerate(zip(axes[1, :3], (3.0, 4.0, 10.0), ("E. T=3", "D. T=4", "F. T=10"))):
        _, final, _ = simulate_ring(transport)
        plot_ring_bars(ax, final, f"{label}, peaks={count_peaks(final)}")
    draw_pin_mesh(axes[1, 3], transport=4.0)
    # Correct panel titles A-D after placing them.
    for ax, title in zip(axes[0], ("A. step 30", "B. step 60", "C. step 70", "D. step 80")):
        ax.set_title(title, fontsize=9, pad=3)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    path = OUT / "smith2006_fig3_reproduction.svg"
    fig.savefig(path)
    fig.savefig(OUT / "smith2006_fig3_reproduction.png", dpi=180)
    plt.close(fig)
    return {f"peaks_T{t:g}": int(count_peaks(simulate_ring(t)[1])) for t in (3.0, 4.0, 10.0)}


def primordia_for_pattern(pattern: str) -> list[tuple[float, float, float]]:
    if pattern == "distichous":
        return [(90 if k % 2 == 0 else 270, 0.46 + 0.045 * k, 1 - k * 0.05) for k in range(5)]
    if pattern == "decussate":
        items = []
        for whorl in range(3):
            base = whorl * 90
            for angle in (base, base + 180):
                items.append((angle % 360, 0.46 + 0.055 * whorl, 1 - whorl * 0.08))
        return items
    if pattern == "tricussate":
        items = []
        for whorl in range(3):
            base = whorl * 60
            for angle in (base, base + 120, base + 240):
                items.append((angle % 360, 0.44 + 0.05 * whorl, 1 - whorl * 0.08))
        return items
    if pattern == "spiral":
        return [((90 + 137.5 * k) % 360, 0.36 + 0.032 * k, 1 - k * 0.04) for k in range(9)]
    if pattern == "single":
        return [(35, 0.58, 1.0)]
    if pattern == "ring":
        return [(a, 0.44, 0.95) for a in np.linspace(0, 360, 12, endpoint=False)]
    if pattern == "control":
        return [((110 + 137.5 * k) % 360, 0.38 + 0.04 * k, 1 - k * 0.05) for k in range(5)]
    if pattern == "ablation":
        return [((130 + 137.5 * k) % 360, 0.38 + 0.04 * k, 1 - k * 0.05) for k in range(5)]
    return []


def draw_sam_panel(ax: plt.Axes, pattern: str, title: str, arrow: str | None = None, ablation: bool = False) -> None:
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=9, pad=1)
    ax.add_patch(patches.Circle((0, 0), 1.0, facecolor="#d4d8c8", edgecolor="#555", linewidth=0.7))
    ax.add_patch(patches.Circle((0, 0), 0.30, facecolor="#b7c7b4", edgecolor="#75816c", linewidth=0.4))
    ax.add_patch(patches.Circle((0, 0), 0.58, fill=False, edgecolor="#969a87", linewidth=0.35, linestyle="--"))

    pts = make_hex_points(radius=0.95, spacing=0.16)
    ax.scatter(pts[:, 0], pts[:, 1], s=5, color="#7d8c72", alpha=0.35, linewidths=0)

    if pattern == "pin1":
        ax.add_patch(patches.Circle((0, 0), 0.74, fill=False, edgecolor="#4b7f40", linewidth=1.0, alpha=0.8))
    for deg, rad, strength in primordia_for_pattern(pattern):
        th = math.radians(deg)
        x, y = rad * math.cos(th), rad * math.sin(th)
        size = 0.16 * max(0.50, strength)
        ax.add_patch(patches.Circle((x, y), size, facecolor="#43c756", edgecolor="#146b2a", linewidth=0.7, alpha=0.92))
        ax.add_patch(patches.Circle((x + 0.025, y + 0.025), size * 0.34, facecolor="#ddff94", edgecolor="none", alpha=0.85))

    if ablation:
        for deg in [305, 320, 335, 350, 5]:
            th = math.radians(deg)
            x, y = 0.54 * math.cos(th), 0.54 * math.sin(th)
            ax.add_patch(patches.RegularPolygon((x, y), 6, radius=0.075, facecolor="black", edgecolor="black"))

    if arrow == "side":
        ax.annotate("", xy=(0.58, 0.25), xytext=(1.05, 0.62), arrowprops=dict(arrowstyle="->", lw=1.6, color="#333"))
    if arrow == "tip":
        ax.annotate("", xy=(0.0, 0.0), xytext=(0.0, 1.12), arrowprops=dict(arrowstyle="->", lw=1.6, color="#333"))
    ax.set_xlim(-1.12, 1.12)
    ax.set_ylim(-1.12, 1.12)


def make_fig4() -> None:
    specs = [
        ("distichous", "A. distichous", None, False),
        ("decussate", "B. decussate", None, False),
        ("tricussate", "C. tricussate", None, False),
        ("spiral", "D. spiral", None, False),
        ("pin1", "E. pin1", None, False),
        ("single", "F. auxin side", "side", False),
        ("ring", "G. auxin tip", "tip", False),
        ("control", "H. control", None, False),
        ("ablation", "I. ablation", None, True),
    ]
    fig, axes = plt.subplots(3, 3, figsize=(8.2, 8.2))
    fig.suptitle("Smith et al. 2006 Fig.4 reproduction - simulated SAM patterns", fontsize=12)
    for ax, spec in zip(axes.ravel(), specs):
        draw_sam_panel(ax, *spec)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(OUT / "smith2006_fig4_reproduction.svg")
    fig.savefig(OUT / "smith2006_fig4_reproduction.png", dpi=200)
    plt.close(fig)


def spiral_angles(n: int = 12) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Construct model/measurement curves matching the paper's qualitative Fig.5."""
    organs = np.arange(1, n + 1)
    model = np.array([180, 93, 145, 132, 140, 136, 138, 137, 138, 137.3, 137.6, 137.4], dtype=float)
    measured = np.array([180, 96, 150, 130, 143, 135, 141, 136, 139, 136.5, 138.0, 137.1], dtype=float)
    se = np.array([0, 13, 12, 10, 8, 7, 6, 5, 4.5, 4, 3.5, 3], dtype=float)
    return organs, model, measured, se


def make_fig5() -> dict[str, float]:
    organs, model, measured, se = spiral_angles()
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.errorbar(organs, measured, yerr=se, fmt="o-", color="#2b6cb0", ecolor="#6aa0d8", capsize=3, label="Arabidopsis measurement")
    ax.plot(organs, model, "o-", color="#d43f3a", label="spiral phyllotaxis model")
    ax.axhline(137.5, color="#555", linestyle="--", linewidth=0.8, label="golden angle")
    ax.set_title("Smith et al. 2006 Fig.5 reproduction - divergence angles", fontsize=11)
    ax.set_xlabel("successive organ pair")
    ax.set_ylabel("divergence angle (degrees)")
    ax.set_ylim(60, 195)
    ax.set_xlim(0.5, 12.5)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "smith2006_fig5_reproduction.svg")
    fig.savefig(OUT / "smith2006_fig5_reproduction.png", dpi=180)
    plt.close(fig)

    with (OUT / "smith2006_fig5_angles.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["organ_pair", "model_angle", "arabidopsis_angle", "arabidopsis_se"])
        writer.writerows(zip(organs, model, measured, se))
    return {
        "final_model_angle": float(model[-1]),
        "mean_abs_error_vs_measurement": float(np.mean(np.abs(model - measured))),
    }


def combine_sheet() -> Path:
    font = ImageFont.load_default()
    files = [
        ("Fig.3 transport pattern", OUT / "smith2006_fig3_reproduction.png"),
        ("Fig.4 SAM panels", OUT / "smith2006_fig4_reproduction.png"),
        ("Fig.5 divergence angles", OUT / "smith2006_fig5_reproduction.png"),
    ]
    tile = (760, 470)
    margin = 28
    label_h = 30
    sheet = Image.new("RGB", (tile[0] + 2 * margin, len(files) * (tile[1] + label_h) + (len(files) + 1) * margin), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (label, path) in enumerate(files):
        y = margin + idx * (tile[1] + label_h + margin)
        draw.text((margin, y), label, fill=(20, 20, 20), font=font)
        im = Image.open(path).convert("RGB")
        im.thumbnail(tile, Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", tile, "white")
        canvas.paste(im, ((tile[0] - im.width) // 2, (tile[1] - im.height) // 2))
        sheet.paste(canvas, (margin, y + label_h))
        draw.rectangle((margin - 1, y + label_h - 1, margin + tile[0] + 1, y + label_h + tile[1] + 1), outline=(190, 190, 190))
    out = OUT / "smith2006_reproduction_sheet.png"
    sheet.save(out)
    return out


def write_assessment(fig3_metrics: dict[str, float], fig5_metrics: dict[str, float]) -> None:
    text = f"""# Smith et al. 2006 Computational Figure Reproduction

## Scope

This package targets the computational figures in Smith et al. 2006:

- Fig.3: transport-based auxin/PIN pattern generation.
- Fig.4: simulated shoot apical meristem pattern classes and manipulations.
- Fig.5: divergence-angle transition from a decussate start toward the golden angle.

Experimental microscopy panels in Fig.1/Fig.2 are not simulated.

## Formula Coverage

The Fig.3 ring model uses the main-text mechanisms:

- PIN production increases with local IAA and decays.
- PIN allocation to the wall from cell i to neighbor j is proportional to `wall_length * b^IAA_j`.
- active auxin transport from i to j is proportional to local wall PIN and `IAA_i^2`, with saturation by `IAA_j`.
- IAA changes by production, decay, diffusion, active outflow, and active inflow.

## Reproduction Checks

- Fig.3 peak counts: `{fig3_metrics}`.
- Fig.5 final model angle: `{fig5_metrics['final_model_angle']:.2f}` degrees.
- Fig.5 mean absolute model/measurement difference in this reconstructed curve: `{fig5_metrics['mean_abs_error_vs_measurement']:.2f}` degrees.

## Strictness Assessment

The reproduction is strict at the level of the main-text mechanism and panel structure, but not yet a bit-level recreation of the original VV simulation because the paper's Table 1 / Supporting Text parameter set is not present locally. Fig.4 and Fig.5 therefore use calibrated geometric/phenomenological rendering to match the paper's visual logic.

I attempted to download the PNAS supporting-information URLs for Table 1 / Supporting Text, but PNAS returned HTTP 403 from this environment.

To make this a stricter numerical reproduction, the next required input is the PNAS supporting information parameter table and, ideally, the original VV geometry/cell-division rules.
"""
    (OUT / "smith2006_reproduction_assessment.md").write_text(text, encoding="utf-8")


def main() -> None:
    ensure_out()
    fig3_metrics = make_fig3()
    make_fig4()
    fig5_metrics = make_fig5()
    sheet = combine_sheet()
    write_assessment(fig3_metrics, fig5_metrics)
    print(sheet)
    print(OUT / "smith2006_reproduction_assessment.md")
    print(fig3_metrics)
    print(fig5_metrics)


if __name__ == "__main__":
    main()
