"""Shared runner for the error-reduction experiments (N06 onwards).

Reports, for each variant and operating point, the statistics that can be compared with data:
dominant angle, spread of P1..P5 relative angles in permutation-free runs (paper: 6.7 deg),
interval CV (paper: 0.22), non-canonical angle fraction (Besnard 2014 wild type: 15%).
"""
import json
from multiprocessing import Pool

import numpy as np

import analysis
import noise_tools
from e10_phase_sub import OP
from model import Sim

FIELD = dict(k_I=1.2, w_I=25.0, tau_I=4.0)             # secondary field used at the low-G point
# operating point closest to the Arabidopsis inflorescence meristem (plastochron ratio ~0.27):
# secondary field on, and the site follows the auxin maximum for tau_c before its position is fixed
ARABIDOPSIS_LIKE = dict(OP, w=2.0, R_c=5.5, R_p=7.5, R_out=14.5, commit="track", tau_c=2.0, **FIELD)
POINTS = {
    "spiral": dict(w=3.0, R_c=3.5),
    "spiral+field": dict(w=3.0, R_c=3.5, **FIELD),
    "lowG+field": dict(w=2.0, R_c=5.5, **FIELD),
    "lowG": dict(w=2.0, R_c=5.5),
    "lowerG+field": dict(w=2.0, R_c=7.0, **FIELD),
    "ring5": dict(w=3.0, R_c=5.0),
    "ring6": dict(w=3.0, R_c=6.0),
    "ring7": dict(w=3.0, R_c=7.0),
    "ring8": dict(w=3.0, R_c=8.0),
    "ring9": dict(w=3.0, R_c=9.0),
}


def one(job):
    point, name, over, seed, t_end = job
    p = dict(OP, t_end=t_end, mesh_seed=seed, seed=seed)
    p.update(POINTS[point]); p.update(over)
    ringw = p.pop("ringw", 2.0)
    p["w"] *= p.pop("_wscale", 1.0)                    # variant-relative change of the sink range
    p.update(R_p=p["R_c"] + ringw, R_out=p["R_c"] + 9.0)
    try:
        sim = Sim(p).run()
    except Exception as e:                              # report failures instead of hiding them
        return dict(point=point, name=name, seed=seed, pattern="ERROR", error=f"{type(e).__name__}: {e}")
    s = analysis.summarize(sim.log, sim.p["gamma"])
    s.update(point=point, name=name, seed=seed, rank=noise_tools.rank_spread(sim.log),
             lag1=noise_tools.divergence_autocorr(sim.log), Th=sim.p["Th"], gamma=sim.p["gamma"])
    return s


def run(variants, points, seeds, out, t_end=600.0, procs=28):
    jobs = [(pt, n, o, s, t_end) for pt in points for n, o in variants.items() for s in seeds]
    with Pool(min(procs, len(jobs))) as pool:
        res = pool.map(one, jobs)
    with open(out, "w") as f:
        for r in res:
            f.write(json.dumps(r) + "\n")
    for pt in points:
        print(f"\n=== {pt}   (paper: angle 137.5, spread 6.7, interval CV 0.22; Besnard WT non-canonical 15%)")
        print("variant                         G    angle  non-canon  perm  intervalCV  regular  clean  spread r1  mean1-5")
        for n in variants:
            rs = [r for r in res if r["point"] == pt and r["name"] == n]
            err = [r for r in rs if r["pattern"] == "ERROR"]
            rs = [r for r in rs if r["pattern"] not in ("ERROR", "none")]
            if not rs:
                print(f"{n:30s} no primordia" + (f"  ({err[0]['error']})" if err else "")); continue
            g = lambda k: float(np.mean([r[k] for r in rs]))
            reg = sum(not r["pattern"].endswith("~") for r in rs)
            clean = [r for r in rs if r.get("jugacy", 9) <= 1 and r["f_perm"] == 0 and r["f_other"] <= 0.03]
            if clean:
                m = np.nanmean(np.array([r["rank"] for r in clean]), axis=0)
                sp = f"{m[0]:6.1f}   {np.nanmean(m[:5]):6.1f}"
            else:
                sp = "    --       --"
            pats = {}
            for r in rs:
                pats[r["pattern"]] = pats.get(r["pattern"], 0) + 1
            print(f"{n:30s} {rs[0]['gamma']*g('gap_mean'):4.2f}  {np.median([r['alpha'] for r in rs]):6.1f}   {100*(1-g('f_alpha')):5.0f}%   "
                  f"{100*g('f_perm'):3.0f}%    {g('gap_cv'):5.2f}     {reg:2d}/{len(rs):<2d}    {len(clean):2d}   {sp}   {pats}")
    return res
