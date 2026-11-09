"""N02: does a transient secondary inhibitory field (Besnard et al. 2014) regularise timing at the
Arabidopsis-like plastochron ratio, where the auxin-only model shows order permutations?"""
import json
import sys
from multiprocessing import Pool

import numpy as np

import analysis
import noise_tools
from e10_phase_sub import OP
from model import Sim


def one(job):
    name, over, seed = job
    p = dict(OP, t_end=600.0, mesh_seed=seed, seed=seed, **over)
    p.update(R_p=p["R_c"] + 2.0, R_out=p["R_c"] + 9.0)
    sim = Sim(p).run()
    s = analysis.summarize(sim.log, sim.p["gamma"])
    s.update(name=name, seed=seed, over=over, rank=noise_tools.rank_spread(sim.log),
             lag1=noise_tools.divergence_autocorr(sim.log))
    return s


def table(res, names):
    print("variant                        G     alpha  f_alpha f_perm f_other  gap_cv  short  spread1-5  regular  patterns")
    for name in names:
        rs = [r for r in res if r["name"] == name and r.get("pattern") != "none"]
        if not rs:
            print(f"{name:28s} no primordia"); continue
        g = lambda k: float(np.mean([r[k] for r in rs]))
        reg = sum((not r["pattern"].endswith("~")) for r in rs)
        pats = {}
        for r in rs:
            pats[r["pattern"]] = pats.get(r["pattern"], 0) + 1
        print(f"{name:28s} {0.03*g('gap_mean'):5.2f}  {np.median([r['alpha'] for r in rs]):6.1f}  {g('f_alpha'):5.2f}  {g('f_perm'):5.2f}  "
              f"{g('f_other'):5.2f}   {g('gap_cv'):5.2f}  {g('frac_short'):5.2f}   {np.nanmean([np.nanmean(r['rank'][:5]) for r in rs]):7.1f}    {reg}/{len(rs)}   {pats}")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "scan"
    geo = dict(w=2.0, R_c=5.5)
    V = {"ref (no field)": dict(geo)}
    if which == "scan":
        for k in (0.4, 0.8):
            for wI in (5.0, 9.0, 14.0):
                for tau in (4.0, 8.0):
                    V[f"k{k} range{wI:g} life{tau:g}"] = dict(geo, k_I=k, w_I=wI, tau_I=tau)
    elif which == "fine":
        for k in (0.8, 1.2, 1.6, 2.4):
            for wI in (14.0, 25.0):
                for tau in (2.0, 3.0, 4.0):
                    V[f"k{k} range{wI:g} life{tau:g}"] = dict(geo, k_I=k, w_I=wI, tau_I=tau)
    nseed = 9 if which == "fine" else 7
    jobs = [(n, o, s) for n, o in V.items() for s in range(1, nseed)]
    with Pool(28) as pool:
        res = pool.map(one, jobs)
    table(res, list(V))
    with open(f"out/n02_{which}.jsonl", "w") as f:
        for r in res:
            f.write(json.dumps(r) + "\n")
