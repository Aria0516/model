"""Model side of PROTOCOL.md section 4: validation of pin1_polarity.py on model snapshots, and the descriptive
radial profile of the frozen main line v2 (kappa_c = 1.0) computed with the same code.

python model_side.py validate      # export a snapshot as wall/cell tables, compare with model.pin_vectors
python model_side.py profile       # main line v2, rin 0 and 2, seeds 1-2, snapshots 1250-1700
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "frozen_v2"))

import mainline as M  # noqa: E402
from model import pin_vectors  # noqa: E402

import pin1_polarity as PP  # noqa: E402

UM = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))["um"]
OUT = HERE / "out"


def export_tables(sim, swapped=True):
    """Wall and cell tables in the data format (lengths in um). P_ij is computed as in model.rhs.

    swapped=True writes the side intensities under the opposite name, as tissue_paredes builds 10-21 do."""
    G, p, A = sim.G, sim.p, sim.A
    src, dst, n = G["src"], G["dst"], G["n"]
    C = p.get("fb_auxin", 1.0) * A + G["cue"]
    E = np.exp(np.clip(G["beta"] * (C - 10.0), -50.0, 50.0))
    wgt = G["lw"] * E[dst]
    Pij = G["Pcell"][src] * wgt / (np.bincount(src, wgt, n) + p["rho0"])[src]
    length = sim.tis.l
    dens = dict(zip(zip(src.tolist(), dst.tolist()), (Pij / length).tolist()))          # density on i's side of wall ij
    und = [(i, j) for i, j in zip(src.tolist(), dst.tolist()) if i < j]
    ln = dict(zip(zip(src.tolist(), dst.tolist()), length.tolist()))
    own_l = np.array([dens[(i, j)] for i, j in und]); own_r = np.array([dens[(j, i)] for i, j in und])
    a, b = ("right", "left") if swapped else ("left", "right")
    w = pd.DataFrame({"left_label": [i + 2 for i, _ in und], "right_label": [j + 2 for _, j in und],
                      "area": [ln[k] * UM for k in und], a + "_PIN1": own_l, b + "_PIN1": own_r,
                      "left_PI": 1.0, "right_PI": 1.0})
    pts = sim.tis.pts * UM
    cells = pd.DataFrame(dict(label=np.arange(n) + 2, center_x=pts[:, 0], center_y=pts[:, 1], center_z=0.0, layer=1,
                              CLV3=np.exp(-(pts ** 2).sum(1) / (2 * (p["R_c"] * UM) ** 2))))
    return w, cells


def index_from_tables(w, cells, swapped=True, cen=(0.0, 0.0)):
    s = PP.sides(w, set(cells.label), swapped)
    return PP.cell_index(s, cells, np.asarray(cen, float))


def validate():
    res = {}
    for name, extra in (("mainline v2, kappa_c = 1.0", {}), ("same, kappa_c = 0", dict(kappa_c=0.0))):
        sim = M.make(rin=2.0, seed=1, t_end=150.0, **extra).run()
        sim._geometry()                                               # graph and state on the same tessellation
        w, cells = export_tables(sim)
        t = index_from_tables(w, cells)
        pv = pin_vectors(sim.A, sim.G, sim.p)
        pts = sim.tis.pts
        rad = np.maximum(np.hypot(pts[:, 0], pts[:, 1]), 1e-9)
        ref = pd.Series(-(pv[:, 0] * pts[:, 0] + pv[:, 1] * pts[:, 1]) / rad, index=np.arange(sim.tis.n) + 2)
        d = (t.I_PIN1 - ref.reindex(t.index)).abs()
        m = (t.r >= PP.MAIN[0]) & (t.r < PP.MAIN[1])
        wrong = index_from_tables(w, cells, swapped=False)
        am = PP.asym_summary(PP.wall_asymmetry(w, cells, np.zeros(2), set(cells.label), True), boot=False)["main"]["PIN1"]
        res[name] = dict(cells=int(len(t)), wall_asymmetry=am["mean"], frac_outer_side_higher=am["frac_outer_side_higher"], max_abs_diff=float(d.max()), I_main=float(t.I_PIN1[m].mean()), I_ref=float(ref.reindex(t.index)[m].mean()),
                         I_PI=float(t.I_PI[m].mean()), I_main_if_sides_misattributed=float(wrong.I_PIN1[(wrong.r >= PP.MAIN[0]) & (wrong.r < PP.MAIN[1])].mean()))
        print(name, res[name])
    OUT.mkdir(exist_ok=True)
    json.dump(res, open(OUT / "model_validation.json", "w"), indent=1)
    assert all(v["max_abs_diff"] < 0.01 for v in res.values()), "export + index must reproduce model.pin_vectors"
    print("VALIDATION PASSED")


def profile():
    rows, asym = [], []
    for rin in M.RHO_IN:
        for seed in (1, 2):
            sim = M.make(rin=rin, seed=seed, snap_dt=50.0).run()
            for sn in sim.snaps:
                if sn["t"] < 1250.0:
                    continue
                pts = sn["pts"] * UM
                r = np.hypot(pts[:, 0], pts[:, 1])
                I = -(sn["pin"][:, 0] * pts[:, 0] + sn["pin"][:, 1] * pts[:, 1]) / np.maximum(r, 1e-9)
                rec = dict(rin=rin, seed=seed, t=sn["t"], main=float(I[(r >= PP.MAIN[0]) & (r < PP.MAIN[1])].mean()))
                for lo, hi in PP.BANDS:
                    rec[f"{lo:.0f}-{hi:.0f}"] = float(I[(r >= lo) & (r < hi)].mean())
                rows.append(rec)
            sim._geometry()                                           # end state: secondary measure with the data code
            w, cells = export_tables(sim)
            a = PP.wall_asymmetry(w, cells, np.zeros(2), set(cells.label), True)
            arec = dict(rin=rin, seed=seed, **PP.asym_summary(a, boot=False))
            asym.append(arec)
            print(f"rin {rin} seed {seed}: primordia {len(sim.log)}  main {np.mean([q['main'] for q in rows if q['rin'] == rin and q['seed'] == seed]):+.4f}"
                  f"  wall asymmetry (end state) {arec['main']['PIN1']['mean']:+.4f}  frac outer higher {arec['main']['PIN1']['frac_outer_side_higher']:.3f}", flush=True)
    OUT.mkdir(exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "model_v2_profile.csv", index=False)
    json.dump(asym, open(OUT / "model_v2_wall_asymmetry.json", "w"), indent=1)
    d = pd.DataFrame(rows)
    print(d.groupby("rin").mean(numeric_only=True).drop(columns=["seed", "t"]).round(4).to_string())


if __name__ == "__main__":
    {"validate": validate, "profile": profile}[sys.argv[1]]()
