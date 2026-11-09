"""Mechanics check for emergent initiation (no pattern statistics): supercritical up-the-gradient PIN polarisation
(b = 3, Smith et al. 2006 SI Table 1) forms convergence points by itself; the flux-reinforced drain of canal.py
follows them. No threshold placement, exclusion radius, follow-then-fix or secondary field.

python proto_e.py
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
from canal import CanalSim  # noqa: E402

GEO = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))
RC = GEO["rc_end"]
RHO = {(r["rc"], r["rin"]): r["rho_far"] for r in GEO["calib"]}


def ring_peaks(sim, level):
    """Local maxima of epidermal auxin in the ring above `level` (a cell higher than all its neighbours)."""
    A, src, dst = sim.A, sim.tis.src, sim.tis.dst
    nbmax = np.full(len(A), -np.inf)
    np.maximum.at(nbmax, src, A[dst])
    ring = (sim.rad >= sim.p["R_c"]) & (sim.rad < sim.p["R_p"])
    return int((ring & (A > nbmax) & (A > level)).sum())


def job(j):
    rin, b, seed = j
    p = C.geo_params(M.RC_START, rin, RHO[(M.RC_START, rin)], RC, t_end=1100.0, mesh_seed=seed, seed=seed, b=b)
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
            ring = (sim.rad >= p["R_c"]) & (sim.rad < p["R_p"])
            rows.append(dict(t=round(sim.t), drain_cells=int(on.sum()), drains_in_ring=int((on & ring).sum()),
                             ring_peaks_above_ign=ring_peaks(sim, p["theta_ign"] * p["A_free"]), logged=len(sim.log),
                             ring_A=round(float(sim.A[ring].mean()), 2), A_max=round(float(sim.A.max()), 1),
                             finite=bool(np.isfinite(sim.A).all())))
    late = [l for l in sim.log if l[0] >= 700]
    return dict(rin=rin, b=b, seed=seed, rows=rows, n_logged=len(sim.log), n_late=len(late),
                late_times=[round(l[0], 1) for l in late[:15]], late_radii=[round(float(np.hypot(l[1], l[2])), 1) for l in late[:15]])


if __name__ == "__main__":
    jobs = [(rin, b, 1) for rin in (0.0, 2.0) for b in (3.0, 2.5)]
    with Pool(len(jobs)) as pool:
        for r in pool.map(job, jobs):
            print(f"\nrho_in {r['rin']:.0f}  b {r['b']}  seed {r['seed']}  logged {r['n_logged']}  after t=700: {r['n_late']}  "
                  f"(final ring {RC:.2f}-{RC + 2:.2f})")
            print("   late start times ", r["late_times"])
            print("   late start radii ", r["late_radii"])
            for row in r["rows"]:
                print("   ", row)
