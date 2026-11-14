"""Centripetal PIN1 polarity from the authors' wall tables (PROTOCOL.md section 4 and revision 1).

The same functions are applied to data tables and to tables exported from a model snapshot (model_side.py).

python pin1_polarity.py            # convention checks first, then the index for every frame under outputs/pin1_single
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "reproductions" / "elife55832" / "outputs" / "pin1_single"
BANDS = ((10.0, 20.0), (20.0, 30.0), (30.0, 40.0), (40.0, 50.0))
MAIN = (15.0, 50.0)
MIN_WALLS, MIN_CELLS, N_BOOT = 3, 20, 1000


def load(walls_csv):
    w = pd.read_csv(walls_csv)
    cells = pd.read_csv(str(walls_csv).replace("_walls.csv", "_cell_data.csv"))
    return w, cells


def centre(l1):
    wt = np.maximum(l1["CLV3"].values, 0)
    return np.array([(wt * l1.center_x).sum() / wt.sum(), (wt * l1.center_y).sum() / wt.sum()])


def convention_checks(w, cells):
    """Revision 1: normal orientation (left -> right) and the sign relation between the authors' wall polarity and
    the named side intensities. Uses no radial information."""
    c = cells.set_index("label")[["center_x", "center_y", "center_z"]]
    ok = w.left_label.isin(c.index) & w.right_label.isin(c.index)
    v = w[ok]
    d = c.loc[v.right_label].values - c.loc[v.left_label].values
    dot = (v[["normal_x", "normal_y", "normal_z"]].values * d).sum(1)
    dot = dot[np.isfinite(dot)]
    pol = w["PIN1_polarity"].values
    diff = (w["right_PIN1"] - w["left_PIN1"]).values
    m = np.isfinite(pol) & (pol != 0) & np.isfinite(diff) & (diff != 0)
    return dict(walls=len(w), normal_left_to_right=float((dot > 0).mean()), n_normal=int(len(dot)),
                polarity_agrees_with_right_minus_left=float((np.sign(pol[m]) == np.sign(diff[m])).mean()), n_polarity=int(m.sum()))


def sides(w, l1_labels, swapped):
    """Long table, one row per (cell, wall): the cell's own-side PIN1 and PI, the wall area and the cell across.

    swapped=True: the column named left_X was sampled on the right cell's side (tissue_paredes builds 10-21)."""
    a, b = ("right", "left") if swapped else ("left", "right")
    L = pd.DataFrame(dict(cell=w.left_label, other=w.right_label, area=w.area, PIN1=w[a + "_PIN1"], PI=w[a + "_PI"]))
    R = pd.DataFrame(dict(cell=w.right_label, other=w.left_label, area=w.area, PIN1=w[b + "_PIN1"], PI=w[b + "_PI"]))
    s = pd.concat([L, R], ignore_index=True)
    s = s[s.cell.isin(l1_labels) & s.other.isin(l1_labels)]
    return s[np.isfinite(s.PIN1) & np.isfinite(s.PI) & (s.PIN1 > 0) & (s.PI > 0) & np.isfinite(s.area) & (s.area > 0)]


def cell_index(s, cells, cen):
    """Per-cell polarity vector p_c = sum(a m e) / sum(a m) in the top-view plane and its centripetal component."""
    xy = cells.set_index("label")[["center_x", "center_y"]]
    e = xy.loc[s.other].values - xy.loc[s.cell].values
    e /= np.maximum(np.hypot(e[:, 0], e[:, 1]), 1e-12)[:, None]
    out = {}
    g = s.assign(ex=e[:, 0], ey=e[:, 1])
    n = g.groupby("cell").size()
    for sig in ("PIN1", "PI"):
        wgt = g.area * g[sig]
        px = (wgt * g.ex).groupby(g.cell).sum() / wgt.groupby(g.cell).sum()
        py = (wgt * g.ey).groupby(g.cell).sum() / wgt.groupby(g.cell).sum()
        out[sig + "_px"], out[sig + "_py"] = px, py
    t = pd.DataFrame(out)
    t = t[n.reindex(t.index) >= MIN_WALLS]
    pos = xy.loc[t.index].values - cen
    r = np.hypot(pos[:, 0], pos[:, 1])
    rhat = pos / np.maximum(r, 1e-12)[:, None]
    t["x"], t["y"], t["r"] = pos[:, 0], pos[:, 1], r
    for sig in ("PIN1", "PI"):
        t["I_" + sig] = -(t[sig + "_px"].values * rhat[:, 0] + t[sig + "_py"].values * rhat[:, 1])
    return t


def wall_asymmetry(w, cells, cen, l1_labels, swapped):
    """Secondary: (outer - inner) / (outer + inner) own-side intensity per wall, weighted by |cos| between the
    cell-to-cell direction and the radial direction. Positive = more signal on the outer cell's side (inward efflux)."""
    a, b = ("right", "left") if swapped else ("left", "right")
    xy = cells.set_index("label")[["center_x", "center_y"]]
    v = w[w.left_label.isin(l1_labels) & w.right_label.isin(l1_labels)]
    pl, pr = xy.loc[v.left_label].values - cen, xy.loc[v.right_label].values - cen
    rl, rr = np.hypot(pl[:, 0], pl[:, 1]), np.hypot(pr[:, 0], pr[:, 1])
    mid = 0.5 * (pl + pr)
    rm = np.hypot(mid[:, 0], mid[:, 1])
    d = pr - pl
    cosr = np.abs((d * mid).sum(1)) / np.maximum(np.hypot(d[:, 0], d[:, 1]) * rm, 1e-12)
    res = dict(r=rm, weight=cosr * v.area.values, cos=cosr)
    for sig in ("PIN1", "PI"):
        ml, mr = v[a + "_" + sig].values, v[b + "_" + sig].values           # own side of the left / right cell
        outer, inner = np.where(rl > rr, ml, mr), np.where(rl > rr, mr, ml)
        res[sig] = (outer - inner) / (outer + inner)
    t = pd.DataFrame(res)
    return t[np.isfinite(t.PIN1) & np.isfinite(t.PI) & np.isfinite(t.weight)]


def asym_summary(a, boot=True, seed=0):
    """Weighted mean of the wall asymmetry in the main band and per radial band; intervals by resampling walls.
    (The radial bands and intervals for this secondary measure were added after the first run: descriptive.)"""
    rng = np.random.default_rng(seed)

    def one(lo, hi):
        v = a[(a.r >= lo) & (a.r < hi)]
        rec = {}
        for sig in ("PIN1", "PI"):
            if len(v) < MIN_CELLS:
                rec[sig] = dict(n=int(len(v)), mean=None)
                continue
            x, wt = v[sig].values, v.weight.values
            rad = v[sig].values[v.cos.values >= 0.5]                   # walls between radially arranged neighbours
            rec[sig] = dict(n=int(len(v)), mean=float(np.average(x, weights=wt)),
                            n_radial=int(len(rad)), frac_outer_side_higher=float((rad > 0).mean()) if len(rad) else None)
            if boot:
                idx = rng.integers(0, len(v), (N_BOOT, len(v)))
                bs = (x[idx] * wt[idx]).sum(1) / wt[idx].sum(1)
                rec[sig]["lo"], rec[sig]["hi"] = (float(q) for q in np.percentile(bs, [2.5, 97.5]))
        return rec

    return dict(main=one(*MAIN), bands=[dict(lo=lo, hi=hi, **one(lo, hi)) for lo, hi in BANDS])


def band_mean(t, col, lo, hi, rng=None):
    v = t.loc[(t.r >= lo) & (t.r < hi), col].values
    if len(v) < MIN_CELLS:
        return dict(n=int(len(v)), mean=None, lo=None, hi=None)
    out = dict(n=int(len(v)), mean=float(v.mean()))
    if rng is not None:
        bs = v[rng.integers(0, len(v), (N_BOOT, len(v)))].mean(1)
        out["lo"], out["hi"] = (float(q) for q in np.percentile(bs, [2.5, 97.5]))
    return out


def summarise(t, seed=0):
    rng = np.random.default_rng(seed)
    t = t.assign(I_diff=t.I_PIN1 - t.I_PI)
    rec = dict(cells=int(len(t)), main={}, bands=[])
    for col in ("I_PIN1", "I_PI", "I_diff"):
        rec["main"][col] = band_mean(t, col, *MAIN, rng=rng)
    for lo, hi in BANDS:
        rec["bands"].append(dict(lo=lo, hi=hi, **{col: band_mean(t, col, lo, hi, rng=rng) for col in ("I_PIN1", "I_PI", "I_diff")}))
    return rec


def authors_vectors(cells, cen):
    """Attached comparison: mean cosine between the authors' cell polarity vector and the inward direction."""
    l1 = cells[cells.layer == 1]
    res = {}
    pos = l1[["center_x", "center_y"]].values - cen
    r = np.hypot(pos[:, 0], pos[:, 1])
    for sig in ("PIN1", "PI"):
        v = l1[[sig + "_polarity_vector_x", sig + "_polarity_vector_y"]].values
        n = np.hypot(v[:, 0], v[:, 1])
        m = np.isfinite(n) & (n > 0) & (r >= MAIN[0]) & (r < MAIN[1])
        cos = -(v[m] * pos[m]).sum(1) / (n[m] * r[m])
        res[sig] = dict(n=int(m.sum()), mean_cos=float(cos.mean()) if m.any() else None)
    return res


def measure(walls_csv, swapped):
    w, cells = load(walls_csv)
    l1 = cells[cells.layer == 1]
    labels = set(l1.label)
    cen = centre(l1)
    s = sides(w, labels, swapped)
    t = cell_index(s, cells, cen)
    a = wall_asymmetry(w, cells, cen, labels, swapped)
    am = a[(a.r >= MAIN[0]) & (a.r < MAIN[1])]
    rec = dict(frame=Path(walls_csv).parent.name, l1_cells=int(len(l1)), walls_used=int(len(s) // 2), **summarise(t))
    rec["wall_asymmetry"] = {sig: float(np.average(am[sig], weights=am.weight)) for sig in ("PIN1", "PI")}
    rec["wall_asymmetry_detail"] = asym_summary(a)
    a.to_csv(HERE / "out" / f"pin1_walls_{rec['frame']}.csv", index=False)
    rec["authors_vectors"] = authors_vectors(cells, cen)
    return rec, t


if __name__ == "__main__":
    files = sorted(DATA.rglob("*_walls.csv"))
    out = HERE / "out"
    out.mkdir(exist_ok=True)
    checks = []
    for f in files:
        c = convention_checks(*load(f))
        checks.append(dict(frame=f.parent.name, **c))
        print(f"[check] {f.parent.name[-28:]:28s} walls {c['walls']:5d}  normal left->right {c['normal_left_to_right']:.3f} (n={c['n_normal']})  "
              f"polarity sign = sign(right - left by name) {c['polarity_agrees_with_right_minus_left']:.3f} (n={c['n_polarity']})")
    json.dump(checks, open(out / "pin1_convention_checks.json", "w"), indent=1)
    nrm = min(c["normal_left_to_right"] for c in checks)
    agree = [c["polarity_agrees_with_right_minus_left"] for c in checks]
    if nrm >= 0.9 and min(agree) >= 0.9:
        swapped = True
        print("=> builds 10-21: named sides are geometrically swapped; own side = the opposite name")
    elif nrm >= 0.9 and max(agree) <= 0.1:
        swapped = False
        print("=> build 23: named sides are geometric; own side = same name")
    else:
        raise SystemExit("=> side attribution undetermined (PROTOCOL revision 1): stop, no index computed")
    recs = []
    for f in files:
        rec, t = measure(f, swapped)
        recs.append(rec)
        t.to_csv(out / f"pin1_cells_{rec['frame']}.csv")
        m = rec["main"]
        print(f"{rec['frame'][-28:]:28s} cells {rec['cells']:4d}  I(PIN1) {m['I_PIN1']['mean']:+.4f} [{m['I_PIN1']['lo']:+.4f},{m['I_PIN1']['hi']:+.4f}]  "
              f"I(PI) {m['I_PI']['mean']:+.4f}  diff {m['I_diff']['mean']:+.4f} [{m['I_diff']['lo']:+.4f},{m['I_diff']['hi']:+.4f}]  "
              f"wall asym PIN1 {rec['wall_asymmetry']['PIN1']:+.4f} PI {rec['wall_asymmetry']['PI']:+.4f}  "
              f"authors cos PIN1 {rec['authors_vectors']['PIN1']['mean_cos']:+.3f} PI {rec['authors_vectors']['PI']['mean_cos']:+.3f}")
        for b in rec["bands"]:
            f3 = lambda d: "  n/a  " if d["mean"] is None else f"{d['mean']:+.4f}"
            print(f"    {b['lo']:.0f}-{b['hi']:.0f} um  n {b['I_PIN1']['n']:4d}  PIN1 {f3(b['I_PIN1'])}  PI {f3(b['I_PI'])}  diff {f3(b['I_diff'])}")
        wa = rec["wall_asymmetry_detail"]
        print(f"    wall asymmetry 15-50 um: PIN1 {wa['main']['PIN1']['mean']:+.4f} [{wa['main']['PIN1']['lo']:+.4f},{wa['main']['PIN1']['hi']:+.4f}]"
              f"  PI {wa['main']['PI']['mean']:+.4f} [{wa['main']['PI']['lo']:+.4f},{wa['main']['PI']['hi']:+.4f}]  | bands PIN1 "
              + " ".join("n/a" if b["PIN1"]["mean"] is None else f"{b['PIN1']['mean']:+.3f}" for b in wa["bands"])
              + "  PI " + " ".join("n/a" if b["PI"]["mean"] is None else f"{b['PI']['mean']:+.3f}" for b in wa["bands"])
              + f"  | radial walls (n={wa['main']['PIN1']['n_radial']}) with outer side higher: PIN1 {wa['main']['PIN1']['frac_outer_side_higher']:.3f} PI {wa['main']['PI']['frac_outer_side_higher']:.3f}")
    json.dump(dict(swapped=swapped, frames=recs), open(out / "pin1_polarity.json", "w"), indent=1)
    med = lambda k: float(np.median([r["main"][k]["mean"] for r in recs]))
    print(f"median over {len(recs)} meristems, 15-50 um: I(PIN1) {med('I_PIN1'):+.4f}  I(PI) {med('I_PI'):+.4f}  diff {med('I_diff'):+.4f}")
    print(f"validity rule: |I(PI)| median {abs(med('I_PI')):.4f} vs half of I(PIN1) median {0.5 * med('I_PIN1'):.4f} -> "
          + ("INVALID (geometry-dominated)" if abs(med("I_PI")) >= 0.5 * med("I_PIN1") else "valid"))
