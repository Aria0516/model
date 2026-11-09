"""Experiment helper: run named parameter variants over several mesh seeds and tabulate."""
import json
import sys
from collections import Counter, defaultdict
from multiprocessing import Pool

import numpy as np

import analysis
from batch import one


def p_gamma(rs):
    from model import DEFAULT
    return rs[0]["over"].get("gamma", DEFAULT["gamma"])


def run_grid(variants, seeds, base=None, out=None, show_runs=True, procs=28):
    jobs = []
    for name, over in variants.items():
        for s in seeds:
            o = dict(base or {}); o.update(over); o.update(mesh_seed=s, seed=s)
            jobs.append((f"{name}|s{s}", o))
    with Pool(min(len(jobs), procs)) as pool:
        res = pool.map(one, jobs)
    by = defaultdict(list)
    for r in res:
        by[r["name"].split("|")[0]].append(r)
        if show_runs:
            line = r.get("error") if r["pattern"] == "ERROR" else analysis.fmt(r)
            print(f"{r['name']:30s} {line}", flush=True)
    print("\n== summary over seeds ==")
    for name in variants:
        rs = [r for r in by[name] if r["pattern"] not in ("ERROR", "none")]
        pats = Counter(r["pattern"] for r in by[name])
        j1 = [r for r in rs if r.get("jugacy", 0) <= 1]
        line = f"{name:26s} "
        if rs:
            m = lambda k: float(np.mean([r[k] for r in rs]))
            line += (f"alpha={np.median([r['alpha'] for r in rs]):6.1f} f_alpha={m('f_alpha'):.2f} f_perm={m('f_perm'):.2f} "
                     f"f_other={m('f_other'):.2f} sd_alpha={m('sd_alpha'):4.1f} gap_cv={m('gap_cv'):.2f} "
                     f"short={m('frac_short'):.2f} G={p_gamma(rs)*m('gap_mean'):.3f} n={m('n'):.0f} "
                     f"ghost={m('ghost'):.1f} ringA={m('ring_A'):.1f} | ")
        line += f"patterns={dict(pats)}"
        if j1:
            line += (f" | jug1: div_sd med={np.median([r['div_sd'] for r in j1]):5.1f} "
                     f"flips/100={100*np.sum([r['flips'] for r in j1])/np.sum([r['ndiv'] for r in j1]):4.1f} "
                     f"run med={np.median([r['longest'] for r in j1]):.0f} "
                     f"Tp_cv={np.mean([r['Tp_cv'] for r in j1]):.2f} G={np.mean([r['G'] for r in j1]):.3f} "
                     f"fold_med={np.median([r['fold_med'] for r in j1]):.1f}")
        print(line, flush=True)
    if out:
        with open(out, "w") as f:
            for r in res:
                f.write(json.dumps(r) + "\n")
    return res
