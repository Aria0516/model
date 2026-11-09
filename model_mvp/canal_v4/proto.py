"""Mechanics check of the canalization drain (no pattern statistics): does c ignite, how large are the drain
patches, are drains started only in the ring, is the integration stable?

python proto.py
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

import run as C  # noqa: E402   calib_v2: geo_params
from canal import CanalSim  # noqa: E402
from layer import TwoLayerSim  # noqa: E402

GEO = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))
RC = GEO["rc_end"]
RHO = {(r["rc"], r["rin"]): r["rho_far"] for r in GEO["calib"]}


def free_flux(rin, t=40.0):
    """Mean inward flux k_v (A - A2) over the ring in the sink-free steady state (rule, no pattern data)."""
    sim = TwoLayerSim(C.geo_params(RC, rin, RHO[(RC, rin)], RC, Th=1e9, t_end=1.0, init_frac=1.0))
    sim.A2 = np.zeros(sim.tis.n)
    A = sim.A.copy()
    for _ in range(int(t / sim.p["dt"])):
        A = sim._step(A)
    ring = (sim.rad >= sim.p["R_c"]) & (sim.rad < sim.p["R_p"])
    return float((sim.p["k_v"] * (A - sim.A2))[ring].mean())


def job(j):
    rin, theta, tau, c0f = j
    import mainline as M
    p = C.geo_params(M.RC_START, rin, RHO[(M.RC_START, rin)], RC, t_end=900.0, mesh_seed=1, seed=1,
                     theta_ign=theta, tau_can=tau, c0_frac=c0f)
    sim = CanalSim(p, dict(T=M.T_RAMP, rc0=M.RC_START, rc1=RC, rho0=RHO[(M.RC_START, rin)], rho1=RHO[(RC, rin)], ds=M.SRC_OFFSET))
    p = sim.p
    rows = []
    for k in range(int(p["t_end"] / p["dt"])):
        sim.t = k * p["dt"]
        if k and k % p["n_geo"] == 0:
            sim._geometry()
        sim.A = sim._step(sim.A)
        if k % 5000 == 0:
            on = sim.c > 0.5 * p["eta"]
            rad = sim.rad
            rows.append(dict(t=round(sim.t), drain_cells=int(on.sum()), max_c=round(float(sim.c.max()), 2),
                             logged=len(sim.log), ring_A=round(float(sim.A[(rad >= p["R_c"]) & (rad < p["R_p"])].mean()), 2),
                             finite=bool(np.isfinite(sim.A).all())))
    starts = [round(float(np.hypot(x, y)), 1) for _, x, y in sim.log]
    late = [l for l in sim.log if l[0] >= 700]
    gaps = np.diff([l[0] for l in late]) if len(late) > 2 else []
    return dict(rin=rin, theta=theta, tau=tau, c0f=c0f, rows=rows, log_radii=starts[-12:], n_logged=len(sim.log),
                min_gap_late=float(np.min(gaps)) if len(gaps) else None, n_late=len(late))


if __name__ == "__main__":
    jobs = [(rin, th, tau, c0f) for rin in (0.0, 2.0) for th in (0.82,) for tau in (2.0,) for c0f in (0.01, 0.03)]
    with Pool(len(jobs)) as pool:
        for r in pool.map(job, jobs):
            print(f"\nrho_in {r['rin']:.0f}  theta {r['theta']}  tau {r['tau']}  c0 {r['c0f']}  logged {r['n_logged']} "
                  f"(after t=700: {r['n_late']}, smallest gap {r['min_gap_late']})  last start radii {r['log_radii']}  (final ring {RC:.2f}-{RC + 2:.2f})")
            for row in r["rows"]:
                print("   ", row)
