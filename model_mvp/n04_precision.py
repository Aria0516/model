"""N04: what sets the angular precision of a locked spiral?

Each variant changes one ingredient at the spiral point. The threshold is tied to the sink-free
ring level (Th_rel), so variants are compared at the same relative threshold. Because every change
also shifts the emergent plastochron ratio G, G is reported next to the spread.
"""
import json
from multiprocessing import Pool

import numpy as np

import analysis
import noise_tools
from e10_phase_sub import OP
from model import Sim

BASE = dict(OP, w=3.0, R_c=3.5, Th_rel=0.82, t_end=900.0)
VARIANTS = {
    "ref": {},
    "founder group x1": dict(avg_nb=1),
    "founder group x2": dict(avg_nb=2),
    "diffusion D=2.5": dict(D=2.5),
    "diffusion D=6": dict(D=6.0),
    "cue A_q=4": dict(A_q=4.0),
    "cue A_q=14": dict(A_q=14.0),
    "sink eta=1.5": dict(eta=1.5),
    "sink eta=6": dict(eta=6.0),
    "memory tau=2": dict(tau_M=2.0),
    "memory tau=8": dict(tau_M=8.0),
    "threshold 0.74": dict(Th_rel=0.74),
    "threshold 0.90": dict(Th_rel=0.90),
    "growth x0.5": dict(gamma=0.015, t_end=1800.0),
    "ring width 3": dict(ringw=3.0),
    "cells 30% smaller": dict(v_div=0.875),
    "gain b=1.7": dict(b=1.7),
    "gain b=2.3": dict(b=2.3),
    "turnover x2": dict(mu=0.6, rho_pz=36.0, rho_cz=4.0, rho_prox=4.0, eta=6.0),
}


def one(job):
    name, over, seed = job
    p = dict(BASE, mesh_seed=seed, seed=seed, **over)
    ringw = p.pop("ringw", 2.0)
    p.update(R_p=p["R_c"] + ringw, R_out=p["R_c"] + 9.0)
    sim = Sim(p).run()
    s = analysis.summarize(sim.log, sim.p["gamma"])
    s.update(name=name, seed=seed, rank=noise_tools.rank_spread(sim.log), lag1=noise_tools.divergence_autocorr(sim.log),
             Th=sim.p["Th"], free=getattr(sim, "free_level", float("nan")))
    return s


if __name__ == "__main__":
    jobs = [(n, o, s) for n, o in VARIANTS.items() for s in range(1, 11)]
    with Pool(28) as pool:
        res = pool.map(one, jobs)
    with open("out/n04.jsonl", "w") as f:
        for r in res:
            f.write(json.dumps(r) + "\n")
    print("paper: spread of P1..P5 after alignment = 6.7 deg\n")
    print("variant              free   Th     G     alpha  regular  clean  spread r1   r5   mean1-5  gap_cv  Rb_sd")
    for name in VARIANTS:
        rs = [r for r in res if r["name"] == name and r.get("pattern") != "none"]
        if not rs:
            print(f"{name:20s} no primordia"); continue
        g = lambda k: float(np.mean([r[k] for r in rs]))
        reg = sum((not r["pattern"].endswith("~")) for r in rs)
        clean = [r for r in rs if r.get("jugacy", 9) <= 1 and r["f_perm"] == 0 and r["f_other"] <= 0.03]
        if clean:
            m = np.nanmean(np.array([r["rank"] for r in clean]), axis=0)
            sp = f"{m[0]:5.1f} {m[4]:5.1f}  {np.nanmean(m[:5]):6.1f}"
        else:
            sp = "   --    --      --"
        print(f"{name:20s} {g('free'):4.2f}  {g('Th'):4.2f}  {g('G'):4.2f}  {np.median([r['alpha'] for r in rs]):6.1f}   "
              f"{reg:2d}/{len(rs)}   {len(clean):2d}    {sp}   {g('gap_cv'):5.2f}  {g('Rb_sd'):5.2f}")
