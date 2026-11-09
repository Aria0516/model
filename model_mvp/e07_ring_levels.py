"""E07: auxin in the competent ring with no primordia at all (Th = infinity).

For each polarisation gain b: does the ring pattern spontaneously, and at what level does it sit?
A smooth ring (small cell-to-cell sd, no peaks) is the regime where position can be read from
the depletion field instead of from noise-seeded nucleation.
"""
from multiprocessing import Pool
import numpy as np
from model import Sim


def one(job):
    b, rp, seed = job
    sim = Sim(dict(t_end=60.0, v_div=1.25, rho_cz=2.0, rho_prox=2.0, Th=1e9, b=b, R_p=rp, mesh_seed=seed, seed=seed,
                   init_frac=1.0))
    stats = []
    steps = int(60.0 / sim.p["dt"])
    for s in range(steps):
        sim.t = s * sim.p["dt"]
        if s and s % sim.p["n_geo"] == 0:
            sim._geometry()
            if sim.t > 40:
                ring = (sim.rad >= sim.p["R_c"]) & (sim.rad < sim.p["R_p"])
                a = sim.A[ring]
                stats.append((a.mean(), a.std(), a.max(), sim.A.max()))
        from model import rhs
        sim.A = np.maximum(sim.A + sim.p["dt"] * rhs(sim.A, sim.G, sim.p), 0.0)
    st = np.array(stats).mean(0)
    return b, rp, seed, st


if __name__ == "__main__":
    jobs = [(b, rp, s) for rp in (6.0, 7.0) for b in (1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 3.0) for s in (1, 2, 3)]
    with Pool(28) as pool:
        res = pool.map(one, jobs)
    print("ring    b    mean   cell-sd   ring-max   tissue-max   (averaged over t=40..60 and 3 seeds)")
    for rp in (6.0, 7.0):
        for b in (1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 3.0):
            st = np.mean([r[3] for r in res if r[0] == b and r[1] == rp], axis=0)
            print(f"4-{rp:g}  {b:4.1f}  {st[0]:5.2f}  {st[1]:6.2f}  {st[2]:8.2f}  {st[3]:9.2f}")
