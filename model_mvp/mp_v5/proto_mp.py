"""Step 1 of PROTOCOL.md: mechanics check only (C1 discrete response patches, C2 no stall, C3 none without transport).

python proto_mp.py
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "frozen_v2"))
sys.path.insert(1, str(HERE.parent / "calib_v2"))
sys.path.insert(2, str(HERE))

import numpy as np  # noqa: E402

import mainline as M  # noqa: E402
import run as C  # noqa: E402
from mp import MPSim  # noqa: E402

GEO = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))
RC = GEO["rc_end"]
RHO = {(r["rc"], r["rin"]): r["rho_far"] for r in GEO["calib"]}
OUT = HERE / "out"


def job(j):
    rin, hill, tau, T = j
    extra = dict(hill_m=hill, tau_m=tau, mesh_seed=1, seed=1)
    if T is not None:                                     # C3: no polar transport, final geometry
        sim = MPSim(C.geo_params(RC, rin, RHO[(RC, rin)], RC, t_end=300.0, T=T, **extra))
        sim.run()
        ring = (sim.rad >= sim.p["R_c"]) & (sim.rad < sim.p["R_p"])
        return dict(rin=rin, hill=hill, tau=tau, T=T, events=len(sim.log), ring_frac=float((sim.m[ring] > 0.5).mean()))
    p = C.geo_params(M.RC_START, rin, RHO[(M.RC_START, rin)], RC, t_end=1100.0, **extra)
    sim = MPSim(p, dict(T=M.T_RAMP, rc0=M.RC_START, rc1=RC, rho0=RHO[(M.RC_START, rin)], rho1=RHO[(RC, rin)], ds=M.SRC_OFFSET))
    p = sim.p
    rows = []
    for k in range(int(p["t_end"] / p["dt"])):
        sim.t = k * p["dt"]
        if k and k % p["n_geo"] == 0:
            sim._geometry()
        sim.A = sim._step(sim.A)
        if p["tau_M"] > 0:
            sim.M += p["dt"] * (sim.A - sim.M) / p["tau_M"]
        if k % 5000 == 0 and k:
            ring = (sim.rad >= p["R_c"]) & (sim.rad < p["R_p"])
            rows.append(dict(t=round(sim.t), ring_frac_on=round(float((sim.m[ring] > 0.5).mean()), 3),
                             ring_patches=len(sim.clusters(within=ring)), events=len(sim.log),
                             ring_A=round(float(sim.A[ring].mean()), 2), finite=bool(np.isfinite(sim.A).all())))
    late = [l for l in sim.log if l[0] >= 700]
    return dict(rin=rin, hill=hill, tau=tau, T=None, rows=rows, events=len(sim.log), late=len(late))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    jobs = [(rin, h, tau, None) for rin in (0.0, 2.0) for h in (4.0, 8.0) for tau in (1.0, 3.0, 8.0)]
    jobs += [(rin, h, tau, 0.0) for rin in (0.0, 2.0) for h in (4.0, 8.0) for tau in (1.0, 8.0)]
    with Pool(len(jobs)) as pool:
        res = pool.map(job, jobs)
    json.dump(res, open(OUT / "proto_mp.json", "w"), indent=1)
    for r in res:
        if r["T"] is None:
            rf = [row["ring_frac_on"] for row in r["rows"] if row["t"] >= 700]
            pt = [row["ring_patches"] for row in r["rows"] if row["t"] >= 700]
            c1 = bool(rf) and max(rf) < 0.3 and max(pt) >= 1
            print(f"rho_in {r['rin']:.0f} n {r['hill']:.0f} tau_m {r['tau']:.0f} | events {r['events']:4d}, after 700: {r['late']:3d} | "
                  f"t>=700 ring fraction responding {rf} patches {pt} | C1 {c1}  C2 {r['late'] > 0}  finite {all(x['finite'] for x in r['rows'])}")
    for r in res:
        if r["T"] is not None:
            print(f"T=0  rho_in {r['rin']:.0f} n {r['hill']:.0f} tau_m {r['tau']:.0f} | events {r['events']}  ring fraction responding {r['ring_frac']:.3f}  C3 {r['events'] == 0}")
