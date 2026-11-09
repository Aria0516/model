"""Cell-to-cell PIN1 variation from the authors' wall quantification (PROTOCOL revisions 2 and 5).

python pin1_measure.py            # every processed frame under reproductions/elife55832/outputs/pin1_single
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "reproductions" / "elife55832" / "outputs" / "pin1_single"
BAND, MIN_NB = (15.0, 50.0), 3


def cell_values(w, cells):
    """P_c and Q_c: mean of ln(side PIN1) and ln(side PI) over the L1 anticlinal walls of cell c (its own side)."""
    side = pd.concat([w[["left_label", "left_PIN1", "left_PI"]].set_axis(["label", "PIN1", "PI"], axis=1),
                      w[["right_label", "right_PIN1", "right_PI"]].set_axis(["label", "PIN1", "PI"], axis=1)])
    side = side[(side.PIN1 > 0) & (side.PI > 0)]
    side = side.assign(lP=np.log(side.PIN1), lQ=np.log(side.PI))
    g = side.groupby("label")[["lP", "lQ"]].mean()
    return g.loc[g.index.isin(cells.label)]


def residual_s(values, nbrs, sel):
    res, ks = [], []
    for c in sel:
        nb = [n for n in nbrs.get(c, ()) if n in values.index]
        if len(nb) >= MIN_NB:
            res.append(values[c] - values[nb].mean())
            ks.append(len(nb))
    if len(res) < 6:
        return float("nan"), len(res), float("nan")
    k = float(np.mean(ks))
    return float(np.std(res) / np.sqrt(1 + 1 / k)), len(res), k


def measure(walls_csv):
    w = pd.read_csv(walls_csv)
    cells = pd.read_csv(str(walls_csv).replace("_walls.csv", "_cell_data.csv"))
    l1 = cells[cells["layer"] == 1]
    wt = np.maximum(l1["CLV3"].values, 0)
    cx, cy = (wt * l1.center_x).sum() / wt.sum(), (wt * l1.center_y).sum() / wt.sum()       # CLV3-weighted centre
    r = pd.Series(np.hypot(l1.center_x - cx, l1.center_y - cy).values, index=l1.label.values)
    v = cell_values(w, l1)
    nbrs = {}
    for a, b in zip(w.left_label, w.right_label):
        nbrs.setdefault(a, set()).add(b)
        nbrs.setdefault(b, set()).add(a)
    sel = [c for c in v.index if BAND[0] <= r.get(c, -1) <= BAND[1]]
    X = v.lP - v.lQ
    sX, nX, k = residual_s(X, nbrs, sel)
    sQ, _, _ = residual_s(v.lQ, nbrs, sel)
    sP, _, _ = residual_s(v.lP, nbrs, sel)
    sigma = float(np.sqrt(max(sX ** 2 - sQ ** 2, 0.0))) if np.isfinite(sX) and np.isfinite(sQ) else float("nan")
    return dict(frame=Path(walls_csv).parent.name, walls=len(w), l1_cells=len(l1), band_cells=len(sel), used=nX, k=k,
                s_X=sX, s_Q=sQ, s_P=sP, sigma_PIN=sigma)


if __name__ == "__main__":
    rows = [measure(f) for f in sorted(DATA.rglob("*_walls.csv"))]
    for r in rows:
        print(f"{r['frame']:45s} walls {r['walls']:5d}  L1 cells {r['l1_cells']:4d}  in band {r['band_cells']:4d}  used {r['used']:4d}  "
              f"neighbours {r['k']:.1f} | s_X {r['s_X']:.3f}  s_PI {r['s_Q']:.3f}  (s_lnPIN1 uncorrected for PI {r['s_P']:.3f})  sigma_PIN {r['sigma_PIN']:.3f}")
    v = np.array([r["sigma_PIN"] for r in rows if np.isfinite(r["sigma_PIN"])])
    if len(v):
        print(f"sigma_PIN median {np.median(v):.3f} over {len(v)} meristems (range {v.min():.3f}-{v.max():.3f}); "
              f"s_X (upper bound) median {np.median([r['s_X'] for r in rows]):.3f}")
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(rows, open(HERE / "out" / "pin1_measure.json", "w"), indent=1)
