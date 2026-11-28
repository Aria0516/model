"""Curvature-only loading for the blind bulge check (step 1). Reads ONLY coordinates and curvature columns."""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

COLS = ["sequence_registered_x", "sequence_registered_y", "sequence_registered_z", "mean_curvature", "gaussian_curvature", "layer"]
FRAMES = ("t00", "t05", "t10")


def load_seq(seq_dir):
    """{frame: DataFrame(x, y, z, H, K)} in the 0 h frame (rigid sequence registration). No signal columns are read."""
    seq_dir = Path(seq_dir)
    out = {}
    for fr in FRAMES:
        f = next(seq_dir.rglob(f"*_{fr}_aligned_L1_normalized_signal_data.csv"))
        d = pd.read_csv(f, usecols=COLS)
        d = d[d.layer == 1]
        out[fr] = pd.DataFrame(dict(x=d.sequence_registered_x.values, y=d.sequence_registered_y.values,
                                    z=d.sequence_registered_z.values, H=d.mean_curvature.values, K=d.gaussian_curvature.values))
    return out


def apex(d0, r_fit=35.0):
    """Geometric apex of the 0 h dome: fit z = a + b x + c y + e (x^2 + y^2) around the nuclei centroid, twice."""
    c = np.array([d0.x.mean(), d0.y.mean()])
    for _ in range(3):
        m = np.hypot(d0.x - c[0], d0.y - c[1]) < r_fit
        X = np.c_[np.ones(m.sum()), d0.x[m], d0.y[m], d0.x[m] ** 2 + d0.y[m] ** 2]
        a, b, cc, e = np.linalg.lstsq(X, d0.z[m], rcond=None)[0]
        c = np.array([-b / (2 * e), -cc / (2 * e)])
    return c


def smooth(d, col, radius):
    xy = d[["x", "y"]].values
    v = d[col].values
    return np.array([np.median(v[nb]) for nb in cKDTree(xy).query_ball_point(xy, radius)])
