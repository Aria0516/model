"""Plan step 3, B2: central-zone / periphery PIN1 signal ratio (wall-based, per unit wall area), PIN1 group only.

Main measure: own-side wall PIN1 / PI, averaged over the walls of L1 cells in a region, weighted by wall area
(the 3D wall area plays the role of the model's wall length). Secondary: the authors' cell table PIN1 / PI
(mostly intracellular signal: eroded-cell sum / cell volume), ratio only.
Regions: centre = CLV3-weighted centroid of L1 cells; CZ radius R_c from the meristem's own CLV3 radial profile
(half of the central level), and, as a fixed alternative, 27.3 um (median of the 21 qDII meristems).
CZ = r < R_c; periphery = R_c <= r < 1.7 R_c.

python b2_regional.py validate     # model snapshot with known central PIN factor
python b2_regional.py data
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import pin1_polarity as PP

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
R_FIXED = 27.3


def clv3_radius(l1, cen, step=3.0):
    r = np.hypot(l1.center_x - cen[0], l1.center_y - cen[1]).values
    v = l1.CLV3.values
    edges = np.arange(0, 60 + step, step)
    prof = np.array([np.median(v[(r >= a) & (r < b)]) if ((r >= a) & (r < b)).sum() >= 5 else np.nan for a, b in zip(edges[:-1], edges[1:])])
    c = np.nanmax(prof[:3]); floor = np.nanmin(prof)
    half = floor + 0.5 * (c - floor)
    mids = 0.5 * (edges[:-1] + edges[1:])
    for k in range(1, len(prof)):
        if np.isfinite(prof[k]) and prof[k] < half and np.isfinite(prof[k - 1]):
            return float(mids[k - 1] + (mids[k] - mids[k - 1]) * (prof[k - 1] - half) / (prof[k - 1] - prof[k]))
    return float("nan")


def wall_region_mean(s, xy, cen, lo, hi):
    """s: side table (cell, other, area, PIN1, PI) from PP.sides; region by the owning cell's radius."""
    pos = xy.loc[s.cell].values - cen
    r = np.hypot(pos[:, 0], pos[:, 1])
    m = (r >= lo) & (r < hi)
    v = (s.PIN1 / s.PI).values[m]; w = s.area.values[m]
    return float(np.sum(v * w) / np.sum(w)), int(m.sum())


def measure(f, swapped=True):
    w, cells = PP.load(f)
    l1 = cells[cells.layer == 1]
    cen = PP.centre(l1)
    s = PP.sides(w, set(l1.label), swapped)
    xy = cells.set_index("label")[["center_x", "center_y"]]
    rec = dict(frame=Path(f).parent.name, R_clv3=clv3_radius(l1, cen))
    for tag, rc in (("own", rec["R_clv3"]), ("fixed", R_FIXED)):
        cz, ncz = wall_region_mean(s, xy, cen, 0.0, rc)
        pz, npz = wall_region_mean(s, xy, cen, rc, 1.7 * rc)
        rec[f"wall_ratio_{tag}"], rec[f"n_walls_cz_{tag}"], rec[f"n_walls_pz_{tag}"] = cz / pz, ncz, npz
        r = np.hypot(l1.center_x - cen[0], l1.center_y - cen[1]).values
        q = (l1.PIN1 / l1.PI).values
        rec[f"cell_ratio_{tag}"] = float(np.median(q[r < rc]) / np.median(q[(r >= rc) & (r < 1.7 * rc)]))
    return rec


def validate():
    sys.path.insert(0, str(HERE))
    import model_side as MS
    import mainline as M
    sim = M.make(rin=2.0, seed=1, t_end=150.0).run()
    sim._geometry()
    w, cells = MS.export_tables(sim)
    rc_um = sim.p["R_c"] * MS.UM
    s = PP.sides(w, set(cells.label), True)
    xy = cells.set_index("label")[["center_x", "center_y"]]
    cz, _ = wall_region_mean(s, xy, np.zeros(2), 0.0, rc_um)
    pz, _ = wall_region_mean(s, xy, np.zeros(2), rc_um, 1.7 * rc_um)
    # direct computation from the model: P_ij / l_ij, length-weighted, by region of the owning cell
    G, p, A = sim.G, sim.p, sim.A
    src, dst, n = G["src"], G["dst"], G["n"]
    C = A + G["cue"]
    E = np.exp(np.clip(G["beta"] * (C - 10.0), -50.0, 50.0))
    wgt = G["lw"] * E[dst]
    Pij = G["Pcell"][src] * wgt / (np.bincount(src, wgt, n) + p["rho0"])[src]
    l = sim.tis.l
    r = sim.rad[src] * MS.UM
    dens = Pij / l
    ref = lambda lo, hi: float(np.sum((dens * l)[(r >= lo) & (r < hi)]) / np.sum(l[(r >= lo) & (r < hi)]))
    out = dict(R_c_um=rc_um, pin_cz=p["pin_cz"], code_ratio=cz / pz, direct_ratio=ref(0, rc_um) / ref(rc_um, 1.7 * rc_um))
    print(out)
    assert abs(out["code_ratio"] - out["direct_ratio"]) < 1e-9, "code must reproduce the model's own wall densities"
    json.dump(out, open(OUT / "b2_validation.json", "w"), indent=1)
    print("VALIDATION PASSED (the model ratio differs from pin_cz because density per wall length also scales with cell size)")


def data():
    recs = [measure(f) for f in sorted(PP.DATA.rglob("*_walls.csv"))]
    for r in recs:
        print(f"{r['frame'][-28:]:28s} own CLV3 radius {r['R_clv3']:5.1f} um | wall ratio CZ/PZ own {r['wall_ratio_own']:.3f} "
              f"(walls {r['n_walls_cz_own']}/{r['n_walls_pz_own']}), fixed 27.3 um {r['wall_ratio_fixed']:.3f} | "
              f"cell-table ratio own {r['cell_ratio_own']:.3f}, fixed {r['cell_ratio_fixed']:.3f}")
    for k in ("wall_ratio_own", "wall_ratio_fixed", "cell_ratio_own", "cell_ratio_fixed"):
        v = [r[k] for r in recs]
        print(f"{k:18s} median {np.median(v):.3f}  range {min(v):.3f}-{max(v):.3f}")
    json.dump(recs, open(OUT / "b2_regional.json", "w"), indent=1)


if __name__ == "__main__":
    {"validate": validate, "data": data}[sys.argv[1]]()
