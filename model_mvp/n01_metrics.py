"""N01: measure positional noise with the statistic the eLife paper actually reports."""
from multiprocessing import Pool

import numpy as np

import analysis
import noise_tools
from e10_phase_sub import OP
from model import Sim

POINTS = {
    "spiral  w3.0 Rc3.5": dict(w=3.0, R_c=3.5),
    "spiral  w3.0 Rc4.0": dict(w=3.0, R_c=4.0),
    "lowG    w2.0 Rc5.5": dict(w=2.0, R_c=5.5),
    "lowG    w2.5 Rc6.5": dict(w=2.5, R_c=6.5),
    "lowG    w3.5 Rc9.0": dict(w=3.5, R_c=9.0),
}


def one(job):
    name, over, seed = job
    p = dict(OP, t_end=900.0, mesh_seed=seed, seed=seed, **over)
    p.update(R_p=p["R_c"] + 2.0, R_out=p["R_c"] + 9.0)
    sim = Sim(p).run()
    s = analysis.summarize(sim.log, sim.p["gamma"])
    return name, seed, s, noise_tools.rank_spread(sim.log), noise_tools.divergence_autocorr(sim.log)


if __name__ == "__main__":
    jobs = [(n, o, s) for n, o in POINTS.items() for s in range(1, 11)]
    with Pool(28) as pool:
        res = pool.map(one, jobs)
    print("eLife 2020: observed spread of P1..P5 after alignment = 6.7 deg (mean over ranks);")
    print("            random-walk model with 3.6 deg per step gives 3.6, 5.2, 6.4, 7.3, 8.1 for ranks 1..5\n")
    print("point                  G     alpha  f_alpha f_perm  spread at rank 1..6 (deg)               mean1-5  lag1-corr  gap_cv  Rb_sd")
    for name in POINTS:
        rs = [r for r in res if r[0] == name and r[2].get("pattern") != "none"]
        S = np.array([r[3] for r in rs]); m = np.nanmean(S, axis=0)
        g = lambda k: float(np.mean([r[2][k] for r in rs]))
        G = 0.03 * g("gap_mean")
        print(f"{name:20s} {G:5.2f}  {np.median([r[2]['alpha'] for r in rs]):6.1f}  {g('f_alpha'):5.2f}  {g('f_perm'):5.2f}   "
              + " ".join(f"{v:5.1f}" for v in m) + f"   {np.nanmean(m[:5]):6.1f}   {np.nanmean([r[4] for r in rs]):+6.2f}   {g('gap_cv'):5.2f}  {g('Rb_sd'):5.2f}")
    # same, restricted to runs without order permutations, to separate the two noise sources
    print("\nruns with no permutation motif only:")
    for name in POINTS:
        rs = [r for r in res if r[0] == name and r[2].get("pattern") != "none" and r[2]["f_perm"] == 0 and r[2]["f_other"] <= 0.05]
        if rs:
            m = np.nanmean(np.array([r[3] for r in rs]), axis=0)
            print(f"{name:20s} n={len(rs):2d}   " + " ".join(f"{v:5.1f}" for v in m) + f"   mean1-5 {np.nanmean(m[:5]):5.1f}   lag1 {np.nanmean([r[4] for r in rs]):+.2f}")
