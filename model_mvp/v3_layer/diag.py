"""Post-hoc diagnostics for the inner-layer study (PROTOCOL addendum): read-out specificity and whether
primordia stay auxin maxima.  Re-runs seeds 1 and 2 of every group; runs are deterministic.

python diag.py
"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import v3_run as V
from layer import TwoLayerSim
from t_types import RampSim

T0, T1, EVERY = 1250.0, 1700.0, 5.0


def sample(sim):
    t = sim.t
    if not (T0 <= t < T1) or abs(t / EVERY - round(t / EVERY)) > 1e-6:
        return
    p, pts, A, R = sim.p, sim.tis.pts, sim.A, sim.R
    if len(A) != len(pts):
        return
    rad = np.hypot(pts[:, 0], pts[:, 1])
    ring = (rad >= p["R_c"]) & (rad < p["R_p"])
    dmin = np.full(len(A), np.inf)
    for q in sim.prim:
        np.minimum(dmin, np.hypot(pts[:, 0] - q["x"], pts[:, 1] - q["y"]), out=dmin)
    for q in sim.inc:
        np.minimum(dmin, np.hypot(pts[:, 0] - q["x"], pts[:, 1] - q["y"]), out=dmin)
    free = dmin > 2 * p["w"]
    ring_free = float(A[ring & free].mean()) if (ring & free).any() else np.nan
    zones = dict(ring=ring, mid=(rad >= p["R_p"]) & (rad < p["R_src"]), far=rad >= p["R_src"])
    rec = dict(t=t, ring_free=ring_free, prims=[],
               R_on={z: float((R[m & free] >= 0.5).mean()) if (m & free).any() else np.nan for z, m in zones.items()},
               A_free={z: float(A[m & free].mean()) if (m & free).any() else np.nan for z, m in zones.items()})
    for q in sim.prim:
        d = np.hypot(pts[:, 0] - q["x"], pts[:, 1] - q["y"])
        k = int(np.argmin(d))
        near = d < p["w"]
        near[k] = True                                     # a primordium at the tissue edge may have no cell within w
        rec["prims"].append((q["id"], t - q["tc"], float(A[k]), float(R[k]), bool(A[k] >= A[near].max() - 1e-9), float(np.hypot(q["x"], q["y"]))))
    sim.diag_rec.append(rec)


class DiagRamp(RampSim):
    def _geometry(self, first=False):
        super()._geometry(first)
        if not first:
            sample(self)


class DiagLayer(TwoLayerSim):
    def _geometry(self, first=False):
        super()._geometry(first)
        if not first:
            sample(self)


def job(j):
    kind, rin, kv, ke, eta2, seed, cal = j
    if kind == "single":
        rho_s, rho_e = cal["single"][f"{V.RC_START}|{rin}"], cal["single"][f"{V.RC_END}|{rin}"]
    else:
        rho_s, rho_e = cal["layer"][V.ckey(V.RC_START, rin, kv)], cal["layer"][V.ckey(V.RC_END, rin, kv)]
    p = V.new_params(V.RC_START, V.KC, V.DS, rin, rho_s, t_end=1700.0, Th=V.TH, mesh_seed=seed, seed=seed, **V.TRACK, **V.READOUT)
    ramp = dict(T=600.0, rc0=V.RC_START, rc1=V.RC_END, rho0=rho_s, rho1=rho_e, ds=V.DS)
    if kind == "single":
        sim = DiagRamp(p, ramp)
    else:
        sim = DiagLayer(dict(p, k_v=kv, K_e=ke, eta2=eta2), ramp)
    sim.diag_rec = []
    sim.run()
    late = [l for l in sim.log if T0 <= l[0] < T1]
    pat = V.analysis.summarize(late, 0.03, skip=0.0)["pattern"] if len(late) >= 12 else "none"
    gap = float(np.mean(np.diff([l[0] for l in late])))
    return dict(kind=kind, rin=rin, kv=kv, ke=ke, eta2=eta2, seed=seed, pattern=pat, gap=gap, rec=sim.diag_rec)


if __name__ == "__main__":
    cal = json.load(open(V.OUT / "calib.json"))
    jobs = [("single", rin, None, None, None, s, cal) for rin in V.RINS for s in (1, 2)]
    jobs += [("layer", rin, kv, ke, e2, s, cal) for rin in V.RINS for kv in V.KVS for ke in V.KES for e2 in V.ETA2S for s in (1, 2)]
    with Pool(28) as pool:
        res = pool.map(job, jobs)
    json.dump(res, open(V.OUT / "diag.json", "w"))
    main = json.load(open(V.OUT / "runs.json"))
    lab = {(r["kind"], r["rin"], r["kv"], r["ke"], r["eta2"], r["seed"]): r["pattern"] for r in main if r["T"] is None}
    mism = [(r["kind"], r["rin"], r["kv"], r["ke"], r["eta2"], r["seed"]) for r in res
            if lab[(r["kind"], r["rin"], r["kv"], r["ke"], r["eta2"], r["seed"])] != r["pattern"]]
    print("pattern labels identical to main run:", not mism, mism)
    print("\naway from primordia (> 2w from every primordium): mean auxin and share of cells with read-out >= 0.5, by zone "
          "(ring; mid = ring edge to source; far = source zone)")
    print("model                          rho_in   auxin ring  mid   far  | read-out on ring  mid   far")
    for kind, rin, kv, ke, e2 in [("single", rin, None, None, None) for rin in V.RINS] + \
            [("layer", rin, kv, ke, e2) for rin in V.RINS for kv in V.KVS for ke in V.KES for e2 in V.ETA2S]:
        rs = [r for r in res if (r["kind"], r["rin"], r["kv"], r["ke"], r["eta2"]) == (kind, rin, kv, ke, e2)]
        a = " ".join(f"{np.nanmean([x['A_free'][z] for r in rs for x in r['rec']]):5.2f}" for z in ("ring", "mid", "far"))
        o = " ".join(f"{np.nanmean([x['R_on'][z] for r in rs for x in r['rec']]):5.2f}" for z in ("ring", "mid", "far"))
        name = "single layer" if kind == "single" else f"k_v={kv:g} K_e={'inf' if ke == 0 else ke} eta2={e2:g}"
        print(f"{name:30s} {rin:5.1f}    {a}  |          {o}")
    print("\nage bins in intervals; ratio = centre auxin / free-ring mean; max = centre is the highest cell within w; R = read-out at centre")
    print("model                          rho_in  free ring | ratio 0-1  1-2  2-3  3-4 | max 0-1  1-2  2-3  3-4 | R 0-1  1-2  2-3  3-4")
    for kind, rin, kv, ke, e2 in [("single", rin, None, None, None) for rin in V.RINS] + \
            [("layer", rin, kv, ke, e2) for rin in V.RINS for kv in V.KVS for ke in V.KES for e2 in V.ETA2S]:
        rs = [r for r in res if (r["kind"], r["rin"], r["kv"], r["ke"], r["eta2"]) == (kind, rin, kv, ke, e2)]
        fr = np.nanmean([x["ring_free"] for r in rs for x in r["rec"]])
        bins = [[], [], [], []]
        for r in rs:
            for x in r["rec"]:
                for pid, age, a, rr, ismax, rad in x["prims"]:
                    b = int(age / r["gap"])
                    if 0 <= b < 4:
                        bins[b].append((a / x["ring_free"], ismax, rr))
        ratio = " ".join(f"{np.median([v[0] for v in b]):4.2f}" for b in bins)
        mx = " ".join(f"{np.mean([v[1] for v in b]):4.2f}" for b in bins)
        rd = " ".join(f"{np.median([v[2] for v in b]):4.2f}" for b in bins)
        name = "single layer" if kind == "single" else f"k_v={kv:g} K_e={'inf' if ke == 0 else ke} eta2={e2:g}"
        print(f"{name:30s} {rin:5.1f}   {fr:6.2f}   | {ratio} | {mx} | {rd}")
