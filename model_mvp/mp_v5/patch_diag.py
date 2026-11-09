"""Mechanics check, continued: what are the recorded 'initiation events'? Follows every response patch
(m > 0.5) between t = 700 and 760 and reports how long patches live and whether they move outwards with the
tissue (a primordium) or blink on and off in the ring. No pattern statistics.

python patch_diag.py <rho_in> <hill> <tau_m>
"""
import math
import sys

import numpy as np

import proto_mp as P
from mp import MPSim

rin, hill, tau = (float(a) for a in sys.argv[1:4])
p = P.C.geo_params(P.M.RC_START, rin, P.RHO[(P.M.RC_START, rin)], P.RC, t_end=760.0, hill_m=hill, tau_m=tau, mesh_seed=1, seed=1)
sim = MPSim(p, dict(T=P.M.T_RAMP, rc0=P.M.RC_START, rc1=P.RC, rho0=P.RHO[(P.M.RC_START, rin)], rho1=P.RHO[(P.RC, rin)], ds=P.M.SRC_OFFSET))
p = sim.p
tracks, nxt = {}, 0           # id -> list of (t, r, theta, size, mean m)
prev = []                     # (id, x, y) of patches at the previous geometry step
for k in range(int(p["t_end"] / p["dt"])):
    sim.t = k * p["dt"]
    if k and k % p["n_geo"] == 0:
        sim._geometry()
        if sim.t >= 700.0:
            g = math.exp(p["gamma"] * p["dt"] * p["n_geo"])
            pts, cur = sim.tis.pts, []
            for cl in sim.clusters():
                w = sim.m[cl]
                x, y = float((w * pts[cl, 0]).sum() / w.sum()), float((w * pts[cl, 1]).sum() / w.sum())
                best = min(prev, key=lambda q: math.hypot(q[1] * g - x, q[2] * g - y), default=None)
                if best is not None and math.hypot(best[1] * g - x, best[2] * g - y) < 1.5:
                    pid = best[0]
                else:
                    pid, nxt = nxt, nxt + 1
                tracks.setdefault(pid, []).append((sim.t, math.hypot(x, y), math.degrees(math.atan2(y, x)), len(cl), float(w.mean())))
                cur.append((pid, x, y))
            prev = cur
    sim.A = sim._step(sim.A)
    if p["tau_M"] > 0:
        sim.M += p["dt"] * (sim.A - sim.M) / p["tau_M"]

ring = (p["R_c"], p["R_p"])
life = np.array([tr[-1][0] - tr[0][0] for tr in tracks.values()])
born_in_ring = [tr for tr in tracks.values() if ring[0] <= tr[0][1] < ring[1] and tr[0][0] > 700.5]
print(f"rho_in {rin:.0f} n {hill:.0f} tau_m {tau:.0f}: {len(tracks)} patches seen in 700-760; recorded events in 700-760: "
      f"{sum(700 <= l[0] < 760 for l in sim.log)}")
print("patch lifetime (time units): quantiles 25/50/75/90 =", np.round(np.quantile(life, [.25, .5, .75, .9]), 2) if len(life) else None)
print(f"patches born in the ring after 700.5: {len(born_in_ring)}; of these living >= 5: {sum(tr[-1][0] - tr[0][0] >= 5 for tr in born_in_ring)}, "
      f">= 20: {sum(tr[-1][0] - tr[0][0] >= 20 for tr in born_in_ring)}")
for tr in sorted(tracks.values(), key=lambda tr: tr[0][0])[:25]:
    print(f"  born t {tr[0][0]:6.2f} r {tr[0][1]:4.1f} th {tr[0][2]:6.1f} size {tr[0][3]:2d} | last t {tr[-1][0]:6.2f} r {tr[-1][1]:4.1f} "
          f"th {tr[-1][2]:6.1f} size {tr[-1][3]:2d} m {tr[-1][4]:.2f} | lived {tr[-1][0] - tr[0][0]:5.2f}")
