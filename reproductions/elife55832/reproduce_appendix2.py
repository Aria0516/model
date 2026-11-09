#!/usr/bin/env python3
"""Modern, NumPy-only reproduction of the paper's Appendix 2 model.

The eLife paper models a population of phyllotactic systems whose divergence
angles and inter-initiation times fluctuate.  This script implements equations
24--34 with one documented correction: equation 30 is interpreted as the
multiplicative recurrence implied by equations 26--29,

    r[p] = r[p-1] * exp(beta * Normal(1, sigma_tau)).

The printed equation uses r[p]-r[p-1] on the left-hand side, which is
dimensionally inconsistent with its exponential right-hand side.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


R_UM = 30.0
ALPHA_DEG = 137.51
BETA = 0.23
P_MAX = 5


def wrap_angle_deg(angle: np.ndarray) -> np.ndarray:
    """Map angles to [-180, 180)."""
    return (angle + 180.0) % 360.0 - 180.0


def simulate_population(
    n_systems: int,
    sigma_alpha_deg: float,
    sigma_tau: float,
    rng: np.random.Generator,
    p_max: int = P_MAX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate ranks, unwrapped angles, and radii for aligned SAM systems."""
    tau0 = rng.uniform(-0.5, 0.5, size=n_systems)
    theta = np.zeros((n_systems, p_max + 1), dtype=np.float64)
    tau = np.repeat(tau0[:, None], p_max + 1, axis=1)

    if p_max:
        angle_steps = rng.normal(ALPHA_DEG, sigma_alpha_deg, size=(n_systems, p_max))
        tau_steps = rng.normal(1.0, sigma_tau, size=(n_systems, p_max))
        theta[:, 1:] = np.cumsum(angle_steps, axis=1)
        tau[:, 1:] += np.cumsum(tau_steps, axis=1)

    radius = R_UM * np.exp(BETA * tau)
    ranks = np.broadcast_to(np.arange(p_max + 1), theta.shape).copy()
    return ranks, theta, radius


def circular_sd_deg(values_deg: np.ndarray) -> float:
    """Circular standard deviation in degrees."""
    angles = np.radians(values_deg)
    resultant = np.hypot(np.mean(np.cos(angles)), np.mean(np.sin(angles)))
    resultant = float(np.clip(resultant, 1e-15, 1.0))
    return math.degrees(math.sqrt(-2.0 * math.log(resultant)))


def rank_deviations(theta: np.ndarray, radius: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    angular_sd = np.array([circular_sd_deg(theta[:, p]) for p in range(theta.shape[1])])
    radial_sd = np.std(radius, axis=0, ddof=1)
    return angular_sd, radial_sd


def polar_features(theta: np.ndarray, radius: np.ndarray) -> np.ndarray:
    """Coordinates used for the Appendix 2 Voronoi/k-means calculation.

    The article describes cylindrical coordinates but does not specify feature
    scaling.  We use wrapped angle divided by the divergence angle and log
    radius divided by beta.  This makes the two coordinates dimensionless and
    prevents degrees from numerically overwhelming micrometres.  The choice is
    explicit because the released sam_spaghetti package does not contain the
    Appendix 2 simulation code.
    """
    angle_feature = wrap_angle_deg(theta) / ALPHA_DEG
    radial_feature = np.log(radius / R_UM) / BETA
    return np.column_stack([angle_feature.ravel(), radial_feature.ravel()])


def noiseless_centroids(p_max: int = P_MAX) -> np.ndarray:
    ranks = np.arange(p_max + 1, dtype=np.float64)
    theta = ranks * ALPHA_DEG
    radius = R_UM * np.exp(BETA * ranks)
    return polar_features(theta[None, :], radius[None, :])


def lloyd_kmeans(points: np.ndarray, initial: np.ndarray, max_iter: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """Small deterministic k-means implementation initialized as in Eq. 32."""
    centroids = initial.astype(np.float64, copy=True)
    labels = np.zeros(points.shape[0], dtype=np.int64)
    for _ in range(max_iter):
        distances = np.sum((points[:, None, :] - centroids[None, :, :]) ** 2, axis=2)
        new_labels = np.argmin(distances, axis=1)
        new_centroids = centroids.copy()
        for k in range(centroids.shape[0]):
            members = points[new_labels == k]
            if len(members):
                new_centroids[k] = members.mean(axis=0)
        if np.array_equal(new_labels, labels) and np.allclose(new_centroids, centroids):
            labels = new_labels
            centroids = new_centroids
            break
        labels = new_labels
        centroids = new_centroids
    return labels, centroids


def separability(
    n_systems: int,
    sigma_alpha_deg: float,
    sigma_tau: float,
    seed: int,
    p_max: int = P_MAX,
) -> float:
    rng = np.random.default_rng(seed)
    ranks, theta, radius = simulate_population(n_systems, sigma_alpha_deg, sigma_tau, rng, p_max)
    points = polar_features(theta, radius)
    labels, _ = lloyd_kmeans(points, noiseless_centroids(p_max))
    return float(np.mean(labels == ranks.ravel()))


def color_for_score(score: float) -> str:
    """Blue-to-yellow color ramp without an external plotting dependency."""
    t = float(np.clip((score - 0.5) / 0.5, 0.0, 1.0))
    stops = np.array([[35, 48, 110], [35, 133, 145], [118, 190, 105], [253, 231, 72]])
    position = t * (len(stops) - 1)
    i = min(int(position), len(stops) - 2)
    rgb = (1.0 - (position - i)) * stops[i] + (position - i) * stops[i + 1]
    return "#" + "".join(f"{int(round(v)):02x}" for v in rgb)


def write_heatmap_svg(path: Path, alpha_grid: np.ndarray, tau_grid: np.ndarray, scores: np.ndarray) -> None:
    width, height = 920, 620
    left, top, plot_w, plot_h = 100, 55, 720, 470
    cw, ch = plot_w / len(alpha_grid), plot_h / len(tau_grid)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.axis{font-size:14px}.title{font-size:20px;font-weight:700}.small{font-size:12px}</style>',
        '<text x="100" y="30" class="title">Appendix 2 phyllotactic-cluster separability</text>',
    ]
    for j, tau in enumerate(tau_grid):
        y = top + plot_h - (j + 1) * ch
        for i, alpha in enumerate(alpha_grid):
            score = scores[j, i]
            x = left + i * cw
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{cw + 0.4:.2f}" height="{ch + 0.4:.2f}" '
                f'fill="{color_for_score(score)}"/>'
            )

    parts += [
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="none" stroke="#222"/>',
        f'<line x1="{left + (3.6-alpha_grid[0])/(alpha_grid[-1]-alpha_grid[0])*plot_w:.2f}" y1="{top}" '
        f'x2="{left + (3.6-alpha_grid[0])/(alpha_grid[-1]-alpha_grid[0])*plot_w:.2f}" y2="{top+plot_h}" stroke="white" stroke-width="2" stroke-dasharray="6,5"/>',
        f'<text x="{left + plot_w/2}" y="585" text-anchor="middle" class="axis">divergence-angle noise σ_alpha (degrees)</text>',
        f'<text x="25" y="{top + plot_h/2}" text-anchor="middle" class="axis" transform="rotate(-90 25 {top + plot_h/2})">plastochron noise σ_tau</text>',
    ]
    for val in [0, 5, 10, 15, 20]:
        x = left + (val - alpha_grid[0]) / (alpha_grid[-1] - alpha_grid[0]) * plot_w
        parts += [f'<line x1="{x}" y1="{top+plot_h}" x2="{x}" y2="{top+plot_h+6}" stroke="#222"/>', f'<text x="{x}" y="{top+plot_h+23}" text-anchor="middle" class="small">{val}</text>']
    for val in [0, 0.25, 0.5, 0.75, 1.0]:
        y = top + plot_h - (val - tau_grid[0]) / (tau_grid[-1] - tau_grid[0]) * plot_h
        parts += [f'<line x1="{left-6}" y1="{y}" x2="{left}" y2="{y}" stroke="#222"/>', f'<text x="{left-12}" y="{y+4}" text-anchor="end" class="small">{val:g}</text>']
    for k, score in enumerate([0.5, 0.6, 0.7, 0.8, 0.9, 1.0]):
        y = top + 30 + k * 32
        parts += [f'<rect x="845" y="{y}" width="20" height="20" fill="{color_for_score(score)}"/>', f'<text x="872" y="{y+15}" class="small">{score:.1f}</text>']
    parts += [
        '<text x="840" y="70" class="small">accuracy</text>',
        '<text x="110" y="548" class="small">Dashed line: paper estimate σ_alpha = 3.6 degrees. Feature scaling is stated in the script.</text>',
        '</svg>',
    ]
    path.write_text("\n".join(parts), encoding="utf-8")


def write_points_svg(path: Path, theta: np.ndarray, radius: np.ndarray) -> None:
    width, height = 760, 760
    cx, cy, scale = width / 2, height / 2 + 15, 3.25
    palette = ["#98f5ff", "#76ee00", "#ffd700", "#ffa500", "#cd2626", "#730000"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#222}.title{font-size:20px;font-weight:700}.small{font-size:12px}</style>',
        '<text x="30" y="32" class="title">Simulated aligned primordia population</text>',
    ]
    for r in [30, 60, 90, 120]:
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r*scale}" fill="none" stroke="#ddd"/>')
        parts.append(f'<text x="{cx+r*scale+4}" y="{cy-4}" class="small">{r} um</text>')
    for p in range(theta.shape[1]):
        a = np.radians(theta[:, p])
        x = cx + scale * radius[:, p] * np.cos(a)
        y = cy - scale * radius[:, p] * np.sin(a)
        color = palette[p % len(palette)]
        for xv, yv in zip(x, y):
            parts.append(f'<circle cx="{xv:.2f}" cy="{yv:.2f}" r="2.1" fill="{color}" fill-opacity="0.42"/>')
        parts.append(f'<circle cx="{38+p*76}" cy="715" r="6" fill="{color}"/><text x="{49+p*76}" y="719" class="small">P{p}</text>')
    parts += ['<text x="30" y="745" class="small">sigma_alpha=3.6 degrees; sigma_tau=0.22; R=30 um; beta=0.23</text>', '</svg>']
    path.write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    parser.add_argument("--seed", type=int, default=55832)
    parser.add_argument("--systems", type=int, default=600)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    ranks, theta, radius = simulate_population(args.systems, 3.6, 0.22, rng)
    angular_sd, radial_sd = rank_deviations(theta, radius)

    alpha_grid = np.linspace(0.0, 20.0, 21)
    tau_grid = np.linspace(0.0, 1.0, 21)
    scores = np.empty((len(tau_grid), len(alpha_grid)), dtype=np.float64)
    for j, sigma_tau in enumerate(tau_grid):
        for i, sigma_alpha in enumerate(alpha_grid):
            scores[j, i] = separability(
                max(250, args.systems // 2), float(sigma_alpha), float(sigma_tau),
                args.seed + 1009 * j + i,
            )

    with (args.output / "appendix2_separability.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["sigma_tau\\sigma_alpha"] + [f"{x:.2f}" for x in alpha_grid])
        for sigma_tau, row in zip(tau_grid, scores):
            writer.writerow([f"{sigma_tau:.2f}"] + [f"{x:.6f}" for x in row])

    with (args.output / "appendix2_rank_deviations.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "angular_sd_deg", "radial_sd_um"])
        for p, a_sd, r_sd in zip(range(P_MAX + 1), angular_sd, radial_sd):
            writer.writerow([p, f"{a_sd:.6f}", f"{r_sd:.6f}"])

    summary = {
        "paper": "Galvan-Ampudia et al., eLife 2020, e55832",
        "seed": args.seed,
        "n_systems": args.systems,
        "parameters": {"R_um": R_UM, "alpha_deg": ALPHA_DEG, "beta": BETA, "sigma_alpha_deg": 3.6, "sigma_tau": 0.22},
        "mean_angular_sd_ranks_1_to_5_deg": float(np.mean(angular_sd[1:6])),
        "paper_observed_angular_sd_deg": 6.7,
        "separability_at_inferred_noise": separability(args.systems, 3.6, 0.22, args.seed + 99991),
        "equation_30_interpretation": "multiplicative radial recurrence consistent with equations 26-29",
        "feature_scaling": "wrapped theta/alpha and log(r/R)/beta; released package lacks Appendix 2 code",
    }
    (args.output / "appendix2_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_heatmap_svg(args.output / "appendix2_separability.svg", alpha_grid, tau_grid, scores)
    write_points_svg(args.output / "appendix2_population.svg", theta, radius)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
