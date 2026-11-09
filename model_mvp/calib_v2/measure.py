"""Calibration inputs (d, CZ radius) and held-out quantities (P0 radius, P0 azimuthal width) from the aligned pipeline output (PROTOCOL.md).

python measure.py <output root containing one directory per meristem> [...]
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def p0(e):
    q = e[(e["primordium"] == 0) & (e["extremum_type"] == "minimum") & (e["radial_distance"] >= 15) & (e["radial_distance"] <= 50)]
    return None if q.empty else q.iloc[0]


def az_width(x, y, a, p0_xy, r_p0, band=5.0, step=15.0):
    """Azimuthal half-depth width of the auxin peak at P0 (PROTOCOL revision 1, item 2); same code for data and model."""
    r = np.hypot(x, y)
    th = np.degrees(np.arctan2(y, x))
    t0 = np.degrees(np.arctan2(p0_xy[1], p0_xy[0]))
    dth = (th - t0 + 180.0) % 360.0 - 180.0
    m = np.abs(r - r_p0) < band
    edges = np.arange(-180.0, 180.0 + step, step)
    centres = 0.5 * (edges[:-1] + edges[1:])
    prof = np.array([a[m & (dth >= lo) & (dth < hi)].mean() if (m & (dth >= lo) & (dth < hi)).any() else np.nan
                     for lo, hi in zip(edges[:-1], edges[1:])])
    k0 = int(np.argmin(np.abs(centres)))
    peak = prof[k0]
    if not np.isfinite(peak):
        return None, "no cells at P0"
    side = []
    for sgn in (1, -1):
        idx = [k0 + sgn * j for j in range(1, int(90 / step) + 1) if 0 <= k0 + sgn * j < len(prof)]
        vals = prof[idx]
        if not np.isfinite(vals).any():
            return None, "empty side"
        low = np.nanmin(vals)
        half = 0.5 * (peak + low)
        prev_c, prev_v, hit = centres[k0], peak, None
        for k in idx:
            v = prof[k]
            if np.isfinite(v) and v <= half:
                hit = prev_c + (centres[k] - prev_c) * (prev_v - half) / max(prev_v - v, 1e-12)
                break
            if np.isfinite(v):
                prev_c, prev_v = centres[k], v
        if hit is None:
            return None, "no half-depth crossing"
        side.append(abs(hit))
    return float(np.radians(sum(side)) * r_p0), "ok"


def measure(seq_dir):
    seq_dir = Path(seq_dir)
    rec = dict(sequence=seq_dir.name, frames=[])
    nn_all = []
    for f in sorted(seq_dir.glob("*/*_aligned_L1_normalized_signal_data.csv")):
        d = pd.read_csv(f)
        e = pd.read_csv(str(f).replace("_aligned_L1_normalized_signal_data.csv", "_aligned_primordia_extrema.csv"))
        P = d[["aligned_x", "aligned_y", "aligned_z"]].values
        nn = cKDTree(P).query(P, k=2)[0][:, 1]
        nn_all.append(nn[d["radial_distance"].values < 60])
        q = p0(e)
        s, why = (az_width(d["aligned_x"].values, d["aligned_y"].values, d["Auxin"].values,
                           (q["aligned_x"], q["aligned_y"]), q["radial_distance"]) if q is not None
                  else (None, "no P0 minimum within 15-50 um"))
        rec["frames"].append(dict(frame=f.parent.name[-3:], clv3_radius=float(d["clv3_radius"].iloc[0]),
                                  p0_radius=None if q is None else float(q["radial_distance"]), width=s, note=why))
    nn = np.concatenate(nn_all) if nn_all else np.array([])
    rec["d"] = float(np.median(nn)) if len(nn) else None
    rec["clv3_radius"] = rec["frames"][0]["clv3_radius"] if rec["frames"] else None
    wid = [fr["width"] for fr in rec["frames"] if fr["width"] is not None]
    rec["p0_width"] = float(np.median(wid)) if wid else None
    t0 = [fr for fr in rec["frames"] if fr["frame"] == "t00"]
    rec["p0_radius_t00"] = t0[0]["p0_radius"] if t0 else None
    rec["p0_width_t00"] = t0[0]["width"] if t0 else None          # the P0 label follows the same organ through the sequence
    return rec


if __name__ == "__main__":
    # a sequence directory holds one sub-directory per time point with the aligned L1 table (searched recursively,
    # since the batch run nests each meristem in its own output directory)
    seqs = sorted({f.parent.parent for root in sys.argv[1:] for f in Path(root).rglob("*_aligned_L1_normalized_signal_data.csv")})
    recs = [measure(p) for p in seqs]
    for r in recs:
        fr = " ".join(f"{x['frame']}:P0 {x['p0_radius'] or float('nan'):.1f} width {x['width'] or float('nan'):.1f} ({x['note']})" for x in r["frames"])
        print(f"{r['sequence']:40s} d {r['d'] or float('nan'):.2f}  CZ {r['clv3_radius'] or float('nan'):.1f}  | {fr}")
    if len(sys.argv) > 1 and recs:
        out = Path(__file__).resolve().parent / "out"
        out.mkdir(exist_ok=True)
        json.dump(recs, open(out / ("measure_" + Path(sys.argv[1]).name + ".json"), "w"), indent=1)
