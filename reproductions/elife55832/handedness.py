"""Decide a meristem's handedness from its aligned L1 data (no manual input).

In the aligned frame produced with the correct orientation, successive primordia (younger -> older) are found at
increasing radius and at +137.5 deg from each other (checked on E27/SAM7 with the authors' orientation -1).
We take local auxin maxima (1 - qDII) in the band 0.8-2.2 x CZ radius, sort them by radius and score the
consecutive angle steps d: sum of cos(d - 137.5) - cos(d + 137.5). Positive: orientation is correct; negative: flip.

python handedness.py <sequence directory> [...]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

GOLDEN = np.radians(137.5)


def maxima(d, r_nb=8.0, band=(0.8, 2.2)):
    xy = d[["aligned_x", "aligned_y"]].values
    a = d["Auxin"].values
    r = np.hypot(xy[:, 0], xy[:, 1])
    rc = d["clv3_radius"].iloc[0]
    tree = cKDTree(xy)
    sm = np.array([a[nb].mean() for nb in tree.query_ball_point(xy, 4.0)])          # light smoothing over ~1 cell
    keep = []
    for i, nb in enumerate(tree.query_ball_point(xy, r_nb)):
        if band[0] * rc <= r[i] <= band[1] * rc and sm[i] >= sm[nb].max() and sm[i] >= np.quantile(sm, 0.7):
            keep.append(i)
    return xy[keep], r[keep]


def score_frame(d):
    xy, r = maxima(d)
    if len(r) < 3:
        return 0.0, len(r)
    th = np.arctan2(xy[:, 1], xy[:, 0])[np.argsort(r)]
    step = np.angle(np.exp(1j * np.diff(th)))
    return float(np.sum(np.cos(step - GOLDEN) - np.cos(step + GOLDEN))), len(r)


def score_sequence(seq_dir):
    seq_dir = Path(seq_dir)
    out = []
    for f in sorted(seq_dir.glob("*/*_aligned_L1_normalized_signal_data.csv")):
        s, n = score_frame(pd.read_csv(f))
        out.append((f.parent.name, s, n))
    return sum(s for _, s, _ in out), out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        total, frames = score_sequence(p)
        print(Path(p).name, f"total {total:+.2f}", " ".join(f"{name[-3:]}:{s:+.2f}(n={n})" for name, s, n in frames),
              "-> keep" if total > 0 else "-> flip")
