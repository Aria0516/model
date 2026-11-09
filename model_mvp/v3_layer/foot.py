"""Post-hoc: static inhibition depth of one old primordium 4 units outside the final ring, for each
inner-layer group, measured exactly as in ../v2_supply/why_types/t_types.footprint_job.

python foot.py
"""
import json
from multiprocessing import Pool

import numpy as np

import v3_run as V
from layer import TwoLayerSim
from model import Sim


def job(j):
    kind, rin, kv, ke, e2, seed, cal = j
    rho = cal["single"][f"{V.RC_END}|{rin}"] if kind == "single" else cal["layer"][V.ckey(V.RC_END, rin, kv)]
    p = V.new_params(V.RC_END, V.KC, V.DS, rin, rho, **V.TRACK, Th=1e9, t_end=1.0, init_frac=1.0, mesh_seed=seed, seed=seed)
    sim = Sim(p) if kind == "single" else TwoLayerSim(dict(p, k_v=kv, K_e=ke, eta2=e2))
    A = sim.A.copy()
    for _ in range(6000):
        A = sim._step(A)
    free = A.copy()
    rg = 0.5 * (sim.p["R_c"] + sim.p["R_p"])
    sim._add_primordium(rg + 4.0, 0.0)
    sim.prim[-1]["tc"] = sim.prim[-1]["t0"] = -1e3
    sim.p["start"] = "seeded"
    sim._geometry(first=True)
    for _ in range(6000):
        A = sim._step(A)
    rad, pts = sim.rad, sim.tis.pts
    ring = (rad >= sim.p["R_c"]) & (rad < sim.p["R_p"])
    th = np.abs(np.degrees(np.arctan2(pts[ring, 1], pts[ring, 0])))
    deficit = 1.0 - A[ring] / free[ring]
    bins = np.arange(0, 181, 15)
    prof = [float(deficit[(th >= lo) & (th < hi)].mean()) for lo, hi in zip(bins[:-1], bins[1:])]
    d = np.hypot(pts[:, 0] - rg - 4.0, pts[:, 1])
    return dict(kind=kind, rin=rin, kv=kv, ke=ke, eta2=e2, seed=seed, prof=prof,
                centre=float(A[np.argmin(d)] / free[np.argmin(d)]))


if __name__ == "__main__":
    cal = json.load(open(V.OUT / "calib.json"))
    groups = [("single", rin, None, None, None) for rin in V.RINS]
    groups += [("layer", rin, kv, ke, e2) for rin in V.RINS for kv in V.KVS for ke in V.KES for e2 in V.ETA2S]
    with Pool(28) as pool:
        res = pool.map(job, [g + (s, cal) for g in groups for s in (1, 2, 3)])
    json.dump(res, open(V.OUT / "footprint.json", "w"))
    print("depth = fractional auxin deficit on the ring at the primordium's azimuth (0-15 deg); centre = auxin at the primordium / before it")
    print("model                          rho_in   depth 0-15   45-60   165-180   centre")
    for g in groups:
        P = np.mean([r["prof"] for r in res if (r["kind"], r["rin"], r["kv"], r["ke"], r["eta2"]) == g], 0)
        c = np.mean([r["centre"] for r in res if (r["kind"], r["rin"], r["kv"], r["ke"], r["eta2"]) == g])
        kind, rin, kv, ke, e2 = g
        name = "single layer" if kind == "single" else f"k_v={kv:g} K_e={'inf' if ke == 0 else ke} eta2={e2:g}"
        print(f"{name:30s} {rin:5.1f}     {P[0]:6.3f}     {P[3]:6.3f}   {P[11]:6.3f}    {c:5.2f}")
