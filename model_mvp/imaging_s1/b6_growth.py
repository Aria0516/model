"""Plan step 3, B6: tissue growth rate from rigidly registered nuclei (method validation on synthetic domes).

Estimator: nuclei of two frames, both in the 0 h frame (rigid registration keeps tissue expansion). Fit the dome
z(r) = a + b r^2 + c r^4 about the apex, map every nucleus to surface coordinates (arc length s from the apex along the
fitted profile, azimuth phi), i.e. an azimuthal equidistant unrolling. Growth on a steady dome moves material points
outward along the surface; for locally uniform growth s' = s * exp(gamma * dt). Scan the dilation factor g and take the
one that minimises the median nearest-neighbour distance from dilated frame-1 points (in an arc-length band) to
frame-2 points. gamma = ln(g) / dt.

python b6_growth.py validate      # synthetic domes, known growth, divisions, missed detections, noise, zero-growth control
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from tissue import Tissue  # noqa: E402

OUT = HERE / "out"
UM = 4.907545364810229
BANDS = ((10.0, 25.0), (25.0, 40.0), (40.0, 52.0))
G_GRID = np.arange(0.95, 1.30, 0.002)


def dome_fit(x, y, z, r_fit=50.0):
    r2 = x ** 2 + y ** 2
    m = r2 < r_fit ** 2
    A = np.c_[np.ones(m.sum()), r2[m], r2[m] ** 2]
    return np.linalg.lstsq(A, z[m], rcond=None)[0]


def unroll(x, y, z):
    """Map nuclei to arc length along the fitted dome profile (apex at the origin of x, y)."""
    a, b, c = dome_fit(x, y, z)
    rr = np.linspace(0, 80, 1601)
    dz = 2 * b * rr + 4 * c * rr ** 3
    s_of_r = np.r_[0, np.cumsum(np.sqrt(1 + dz[1:] ** 2) * np.diff(rr))]
    r = np.hypot(x, y)
    s = np.interp(r, rr, s_of_r)
    phi = np.arctan2(y, x)
    return s * np.cos(phi), s * np.sin(phi), s


def estimate(p1, p2, dt_h, band):
    """p1, p2: (N, 3) nuclei of two frames, apex-centred. Returns gamma per hour for the arc-length band."""
    u1x, u1y, s1 = unroll(*p1.T)
    u2x, u2y, s2 = unroll(*p2.T)
    tree = cKDTree(np.c_[u2x, u2y])
    lo, hi = band
    best, score = None, []
    for g in G_GRID:
        m = (s1 * g >= lo) & (s1 * g < hi)
        if m.sum() < 15:
            score.append(np.inf); continue
        d, _ = tree.query(np.c_[u1x[m] * g, u1y[m] * g])
        score.append(np.median(d))
    k = int(np.argmin(score))
    return math.log(G_GRID[k]) / dt_h, float(score[k])


def synthetic(gamma_h, dt_h=5.0, miss=0.15, noise_xy=0.7, noise_z=1.0, seed=0, R_disc_um=70.0, dome_r_um=60.0):
    """Flat model tissue in unrolled (arc-length) coordinates, grown by exp(gamma dt), then wrapped onto a fixed dome."""
    rng = np.random.default_rng(seed)
    tis = Tissue(R_disc_um / UM, seed=seed, v_div=1.25)
    pts0 = tis.pts.copy() * UM
    steps = 20
    g_step = math.exp(gamma_h * dt_h / steps)
    for _ in range(steps):
        parent = tis.grow(g_step)
    pts1 = tis.pts.copy() * UM

    def wrap(p):
        s = np.hypot(p[:, 0], p[:, 1]); phi = np.arctan2(p[:, 1], p[:, 0])
        r = dome_r_um * np.sin(np.minimum(s / dome_r_um, np.pi / 2 * 0.98))        # spherical cap, fixed shape
        z = dome_r_um * np.cos(np.minimum(s / dome_r_um, np.pi / 2 * 0.98)) - dome_r_um
        out = np.c_[r * np.cos(phi), r * np.sin(phi), z]
        keep = (rng.random(len(out)) > miss) & (s < 62.0)                           # missed detections; crop
        out = out[keep]
        out[:, :2] += noise_xy * rng.standard_normal((len(out), 2))
        out[:, 2] += noise_z * rng.standard_normal(len(out))
        return out
    return wrap(pts0), wrap(pts1)


def validate():
    true_rates = (0.0, 0.010, 0.019, 0.030)          # per hour; 0.019 = rate implied by G = 0.23 over 12 h
    rows = []
    for gt in true_rates:
        for seed in range(6):
            for miss in (0.10, 0.20):
                p1, p2 = synthetic(gt, miss=miss, seed=seed)
                for band in BANDS:
                    est, sc = estimate(p1, p2, 5.0, band)
                    rows.append(dict(true=gt, seed=seed, miss=miss, band=f"{band[0]:g}-{band[1]:g}", est=est, score=sc))
    OUT.mkdir(exist_ok=True)
    json.dump(rows, open(OUT / "b6_validation.json", "w"), indent=1)
    import pandas as pd
    d = pd.DataFrame(rows)
    d["rel_err"] = np.where(d.true > 0, (d.est - d.true) / d.true.where(d.true > 0, np.nan), np.nan)
    g = d.groupby(["true", "band"]).agg(est_median=("est", "median"), est_min=("est", "min"), est_max=("est", "max"),
                                        rel_err_median=("rel_err", "median"), rel_err_maxabs=("rel_err", lambda v: np.nanmax(np.abs(v)) if v.notna().any() else np.nan))
    print(g.round(4).to_string())
    print("\nstandard: |relative error| <= 0.15 in the target band; zero-growth control shows no spurious growth (|est| <= 0.15 x 0.019 = 0.0029 /h)")


if __name__ == "__main__":
    {"validate": validate}[sys.argv[1]]()
