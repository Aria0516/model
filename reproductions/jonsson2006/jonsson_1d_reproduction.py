"""Minimal reproduction of Jonsson et al. 2006 simplified phyllotaxis model.

This script implements the one-dimensional periodic-cell version of the
auxin-driven polarized transport model described around Eq. 1 in:

Jonsson et al. 2006, "An auxin-driven polarized transport model for
phyllotaxis", PNAS 103:1633-1638.

The implementation uses the quasi-steady PIN allocation derived from the
PIN cycling model:

    P_ij = P_tot * A_j / sum_k A_k

where k runs over the neighbors of cell i. With two neighbors on a ring,
each cell allocates PIN toward the neighbor with higher auxin. The auxin
dynamics are:

    dA_i/dt = D sum_k (A_k - A_i)
              + T sum_k (A_k P_ki - A_i P_ik)

For D / (T P_tot) below the instability threshold, a nearly homogeneous
auxin distribution breaks into a regular peak-trough pattern.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


def pin_allocation(A: np.ndarray, p_tot: float, eps: float) -> tuple[np.ndarray, np.ndarray]:
    """Return PIN allocation from each cell toward left and right neighbors."""
    left_auxin = np.roll(A, 1)
    right_auxin = np.roll(A, -1)
    denom = left_auxin + right_auxin + eps
    p_to_left = p_tot * left_auxin / denom
    p_to_right = p_tot * right_auxin / denom
    return p_to_left, p_to_right


def auxin_rhs(A: np.ndarray, diffusion: float, transport: float, p_tot: float, eps: float) -> np.ndarray:
    """Compute dA/dt for the 1D ring model."""
    left_auxin = np.roll(A, 1)
    right_auxin = np.roll(A, -1)

    p_to_left, p_to_right = pin_allocation(A, p_tot, eps)

    left_left_auxin = np.roll(A, 2)
    right_right_auxin = np.roll(A, -2)

    # PIN from the left neighbor toward current cell i.
    p_left_to_i = p_tot * A / (left_left_auxin + A + eps)
    # PIN from the right neighbor toward current cell i.
    p_right_to_i = p_tot * A / (right_right_auxin + A + eps)

    passive = diffusion * (left_auxin + right_auxin - 2.0 * A)
    active_in = left_auxin * p_left_to_i + right_auxin * p_right_to_i
    active_out = A * (p_to_left + p_to_right)
    active = transport * (active_in - active_out)
    return passive + active


def rk4_step(A: np.ndarray, dt: float, diffusion: float, transport: float, p_tot: float, eps: float) -> np.ndarray:
    """Advance one RK4 step."""
    k1 = auxin_rhs(A, diffusion, transport, p_tot, eps)
    k2 = auxin_rhs(A + 0.5 * dt * k1, diffusion, transport, p_tot, eps)
    k3 = auxin_rhs(A + 0.5 * dt * k2, diffusion, transport, p_tot, eps)
    k4 = auxin_rhs(A + dt * k3, diffusion, transport, p_tot, eps)
    return A + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def simulate(
    n_cells: int,
    diffusion: float,
    transport: float,
    p_tot: float,
    dt: float,
    steps: int,
    sample_every: int,
    seed: int,
    noise: float,
    eps: float = 1e-12,
) -> tuple[np.ndarray, np.ndarray]:
    """Run the model and return sampled times and auxin history."""
    rng = np.random.default_rng(seed)
    A = 1.0 + noise * rng.standard_normal(n_cells)
    A = np.maximum(A, eps)
    A *= n_cells / A.sum()

    times: list[float] = []
    history: list[np.ndarray] = []
    for step in range(steps + 1):
        if step % sample_every == 0:
            times.append(step * dt)
            history.append(A.copy())

        if step == steps:
            break

        A = rk4_step(A, dt, diffusion, transport, p_tot, eps)
        # Small dt should keep positivity, but this guard avoids numerical
        # failure near depleted troughs. Renormalization preserves total auxin.
        A = np.maximum(A, eps)
        A *= n_cells / A.sum()

    return np.asarray(times), np.asarray(history)


def count_peaks(A: np.ndarray, threshold: float = 1.05) -> int:
    """Count local maxima above threshold on the ring."""
    return int(np.sum((A > np.roll(A, 1)) & (A > np.roll(A, -1)) & (A > threshold)))


def write_csv(path: Path, times: np.ndarray, history: np.ndarray) -> None:
    """Write sampled auxin history to CSV."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "cell", "auxin"])
        for t, row in zip(times, history):
            for cell, value in enumerate(row):
                writer.writerow([f"{t:.8g}", cell, f"{value:.10g}"])


def polyline(points: list[tuple[float, float]], stroke: str, width: float = 2.0) -> str:
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return f'<polyline points="{coords}" fill="none" stroke="{stroke}" stroke-width="{width}" />'


def write_svg(path: Path, cases: list[dict[str, object]]) -> None:
    """Write a compact SVG with final profiles and time heatmaps."""
    width = 980
    height = 720
    margin = 58
    panel_w = 400
    panel_h = 210
    heat_h = 170
    colors = ["#2166ac", "#b2182b"]

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>",
        "text{font-family:Arial,sans-serif;fill:#222}",
        ".axis{stroke:#333;stroke-width:1}",
        ".grid{stroke:#ddd;stroke-width:1}",
        "</style>",
        '<rect width="100%" height="100%" fill="white" />',
        '<text x="32" y="36" font-size="22" font-weight="700">Jonsson et al. 2006 simplified 1D model</text>',
        '<text x="32" y="60" font-size="13">Auxin-driven PIN allocation on a periodic cell ring. Lower D/(TP) breaks uniformity; higher D/(TP) stays nearly uniform.</text>',
    ]

    for idx, case in enumerate(cases):
        x0 = margin + idx * (panel_w + 60)
        y0 = 96
        label = str(case["label"])
        final = np.asarray(case["final"])
        history = np.asarray(case["history"])
        ratio = float(case["ratio"])
        peaks = int(case["peaks"])

        lines.append(f'<text x="{x0}" y="{y0 - 18}" font-size="15" font-weight="700">{label}</text>')
        lines.append(f'<text x="{x0}" y="{y0}" font-size="12">D/(TP)={ratio:.2f}, final peaks={peaks}, std={final.std():.3f}</text>')

        # Final profile panel.
        plot_y = y0 + 26
        max_y = max(1.05, float(final.max()) * 1.05)
        for frac in [0.0, 0.5, 1.0]:
            yy = plot_y + panel_h - frac * panel_h
            lines.append(f'<line class="grid" x1="{x0}" y1="{yy:.2f}" x2="{x0 + panel_w}" y2="{yy:.2f}" />')
            lines.append(f'<text x="{x0 - 38}" y="{yy + 4:.2f}" font-size="10">{frac * max_y:.1f}</text>')
        lines.append(f'<line class="axis" x1="{x0}" y1="{plot_y + panel_h}" x2="{x0 + panel_w}" y2="{plot_y + panel_h}" />')
        lines.append(f'<line class="axis" x1="{x0}" y1="{plot_y}" x2="{x0}" y2="{plot_y + panel_h}" />')
        pts = []
        for c, value in enumerate(final):
            x = x0 + panel_w * c / (len(final) - 1)
            y = plot_y + panel_h - panel_h * float(value) / max_y
            pts.append((x, y))
        lines.append(polyline(pts, colors[idx], 2.2))
        lines.append(f'<text x="{x0 + panel_w / 2 - 24}" y="{plot_y + panel_h + 34}" font-size="12">cell index</text>')
        lines.append(f'<text x="{x0 - 46}" y="{plot_y - 12}" font-size="12">auxin</text>')

        # Heatmap panel.
        heat_y = plot_y + panel_h + 64
        rows, cols = history.shape
        vmin = 0.0
        vmax = max(1.05, float(history.max()))
        cell_w = panel_w / cols
        row_h = heat_h / rows
        for r in range(rows):
            for c in range(cols):
                v = (float(history[r, c]) - vmin) / (vmax - vmin)
                v = min(1.0, max(0.0, v))
                red = int(255 * v + 245 * (1.0 - v))
                green = int(245 * (1.0 - v) + 92 * v)
                blue = int(245 * (1.0 - v) + 55 * v)
                x = x0 + c * cell_w
                y = heat_y + r * row_h
                lines.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell_w + 0.05:.2f}" height="{row_h + 0.05:.2f}" fill="rgb({red},{green},{blue})" />')
        lines.append(f'<rect x="{x0}" y="{heat_y}" width="{panel_w}" height="{heat_h}" fill="none" stroke="#333" stroke-width="1" />')
        lines.append(f'<text x="{x0}" y="{heat_y - 8}" font-size="12">sampled trajectory, time top to bottom</text>')
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(path: Path, cases: list[dict[str, object]], args: argparse.Namespace) -> None:
    rows = []
    for case in cases:
        rows.append(
            f"| {case['label']} | {case['ratio']:.3f} | {case['peaks']} | "
            f"{float(np.asarray(case['final']).std()):.4f} | "
            f"{float(np.asarray(case['final']).min()):.4f} | "
            f"{float(np.asarray(case['final']).max()):.4f} |"
        )

    text = f"""# Jonsson et al. 2006 minimal reproduction

This run implements the one-dimensional periodic simplified model around Eq. 1.

Parameters:

- cells: `{args.cells}`
- time step: `{args.dt}`
- steps: `{args.steps}`
- transport `T`: `{args.transport}`
- total membrane PIN `P`: `{args.pin}`
- seed: `{args.seed}`
- initial noise amplitude: `{args.noise}`

| case | D/(TP) | final peak count | final std | final min | final max |
|---|---:|---:|---:|---:|---:|
{chr(10).join(rows)}

Interpretation: when active transport feedback dominates diffusion, the near-uniform auxin state breaks into a peak-trough pattern. When diffusion is too strong, the uniform state remains stable.
"""
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cells", type=int, default=50)
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--dt", type=float, default=0.02)
    parser.add_argument("--sample-every", type=int, default=200)
    parser.add_argument("--transport", type=float, default=1.0)
    parser.add_argument("--pin", type=float, default=1.0)
    parser.add_argument("--noise", type=float, default=1e-3)
    parser.add_argument("--seed", type=int, default=3)
    parser.add_argument("--outdir", type=Path, default=Path(__file__).resolve().parent / "outputs")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    diffusion_cases = [
        ("pattern-forming", 0.10),
        ("uniform-stable", 0.55),
    ]

    cases: list[dict[str, object]] = []
    for label, diffusion in diffusion_cases:
        times, history = simulate(
            n_cells=args.cells,
            diffusion=diffusion,
            transport=args.transport,
            p_tot=args.pin,
            dt=args.dt,
            steps=args.steps,
            sample_every=args.sample_every,
            seed=args.seed,
            noise=args.noise,
        )
        final = history[-1]
        ratio = diffusion / (args.transport * args.pin)
        peaks = count_peaks(final)
        case = {
            "label": label,
            "diffusion": diffusion,
            "ratio": ratio,
            "times": times,
            "history": history,
            "final": final,
            "peaks": peaks,
        }
        cases.append(case)
        write_csv(args.outdir / f"{label}_history.csv", times, history)

    write_svg(args.outdir / "jonsson_1d_reproduction.svg", cases)
    write_summary(args.outdir / "README.md", cases, args)

    for case in cases:
        final = np.asarray(case["final"])
        print(
            f"{case['label']}: D/(TP)={case['ratio']:.3f}, "
            f"peaks={case['peaks']}, std={final.std():.4f}, "
            f"min={final.min():.4f}, max={final.max():.4f}"
        )
    print(f"wrote outputs to {args.outdir}")


if __name__ == "__main__":
    main()
