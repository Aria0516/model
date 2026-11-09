"""Why does the small-to-large start lead to decussate patterns and more irregular runs?  See PROTOCOL.md.

python ramp_mech.py run | report
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "why_types"))

import numpy as np  # noqa: E402

import analysis  # noqa: E402
from s1_supply import TARGET_LEVEL, TH_REL  # noqa: E402
from t_types import CONFIGS, RC_END, RC_START, TRACK, RampSim, lab, new_params  # noqa: E402

OUT = HERE / "out"
CAL = json.load(open(HERE.parent / "why_types" / "out" / "calib.json"))
RAMP_T = 600.0


def ring_at(t):
    return RC_START + min(t / RAMP_T, 1.0) * (RC_END - RC_START)


def job(j):
    cfg, variant, seed, t_end = j
    kc, ds, rin = cfg
    tr = dict(TRACK)
    if variant == "life8":
        tr["tau_I"] = 8.0
    elif variant == "life16":
        tr["tau_I"] = 16.0
    elif variant == "nofield":
        tr["k_I"] = 0.0
    rho_end, rho_start = CAL[f"{RC_END}|{ds}|{rin}"], CAL[f"{RC_START}|{ds}|{rin}"]
    p = new_params(RC_START, kc, ds, rin, rho_start, t_end=t_end, Th=TH_REL * TARGET_LEVEL, mesh_seed=seed, seed=seed, **tr)
    sim = RampSim(p, dict(T=RAMP_T, rc0=RC_START, rc1=RC_END, rho0=rho_start, rho1=rho_end, ds=ds)).run()
    return dict(cfg=list(cfg), variant=variant, seed=seed, t_end=t_end, log=[[round(a, 3), round(b, 4), round(c, 4)] for a, b, c in sim.log])


def late(log, t0, t1):
    return [l for l in log if t0 <= l[0] < t1]


def pattern(log, t0, t1):
    sub = late(log, t0, t1)
    if len(sub) < 12:
        return "none"
    return analysis.summarize(sub, 0.03, skip=0.0)["pattern"]


def window_labels(log, size=14, step=7):
    out = []
    for i in range(0, max(len(log) - size + 1, 0), step):
        sub = log[i:i + size]
        s = analysis.summarize(sub, 0.03, skip=0.0)
        out.append((float(np.mean([l[0] for l in sub])), s["pattern"]))
    return out


def pair_lags(log, t0, t1):
    """Time between the two members of each two-organ node in the analysed period."""
    sub = late(log, t0, t1)
    t = np.array([l[0] for l in sub])
    th = np.degrees(np.arctan2([l[2] for l in sub], [l[1] for l in sub])) % 360
    grp, _ = analysis.nodes(t, th)
    return [float(t[g[1]] - t[g[0]]) for g in grp if len(g) == 2]


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    if which == "run":
        jobs = [(cfg, "ref", s, 1700.0) for cfg in CONFIGS for s in range(1, 17)]
        jobs += [(cfg, v, s, 1100.0) for cfg in CONFIGS for v in ("life8", "life16", "nofield") for s in range(1, 9)]
        with Pool(28) as pool:
            res = pool.map(job, jobs)
        json.dump(res, open(OUT / "runs.json", "w"))
        print("done", len(res))
    elif which == "report":
        res = json.load(open(OUT / "runs.json"))
        base = lambda p: p.rstrip("~")
        # H-a (1): within-pair lags in reference runs that end decussate
        lags = []
        for r in res:
            if r["variant"] == "ref" and pattern(r["log"], 650, 1100) == "decussate":
                lags += pair_lags(r["log"], 650, 1100)
        print(f"H-a (1)  lag between the two members of a pair (reference runs ending decussate): median {np.median(lags):.1f}, "
              f"quartiles {np.percentile(lags, 25):.1f}-{np.percentile(lags, 75):.1f} (n = {len(lags)} pairs); mean interval between nodes is listed below")
        # H-a (2): decussate share vs field lifetime, by local production
        print("H-a (2)  outcome at 650-1100 by secondary-field setting (first 8 seeds of the reference for comparability)")
        print("  local prod.   setting      runs  spiral  lucas  decussate  distichous  other regular  irregular")
        for rin in (0.0, 2.0):
            for v in ("nofield", "ref", "life8", "life16"):
                rs = [r for r in res if r["cfg"][2] == rin and r["variant"] == v and (v != "ref" or r["seed"] <= 8)]
                pats = [pattern(r["log"], 650, 1100) for r in rs]
                cnt = lambda k: sum(p == k for p in pats)
                other = sum((not p.endswith("~")) and p not in ("spiral", "lucas", "decussate", "distichous", "none") for p in pats)
                irr = sum(p.endswith("~") or p == "none" for p in pats)
                name = {"nofield": "no field", "ref": "lifetime 4", "life8": "lifetime 8", "life16": "lifetime 16"}[v]
                print(f"  {rin:4.1f}          {name:11s}  {len(rs):3d}   {cnt('spiral'):5d}  {cnt('lucas'):5d}  {cnt('decussate'):8d}  {cnt('distichous'):9d}  {other:12d}  {irr:8d}")
        # H-b: first regular non-distichous window along the ramp
        print("H-b  along the ramp (reference runs): first regular window that is not distichous")
        for rin in (0.0, 2.0):
            firsts, starts = [], []
            for r in res:
                if r["variant"] != "ref" or r["cfg"][2] != rin:
                    continue
                w = window_labels(r["log"])
                starts.append(next((p for t, p in w if not p.endswith("~") and p != "none"), "none"))
                f = next(((t, p) for t, p in w if not p.endswith("~") and p not in ("distichous", "none", "intermediate")), None)
                firsts.append(f)
            c = {}
            for f in firsts:
                k = f[1] if f else "never"
                c[k] = c.get(k, 0) + 1
            rings = [ring_at(f[0]) for f in firsts if f]
            s0 = {}
            for s in starts:
                s0[s] = s0.get(s, 0) + 1
            print(f"  local production {rin:g}: first regular window overall {s0}; first non-distichous regular window {c}; "
                  f"ring inner radius at that moment: median {np.median(rings) if rings else float('nan'):.2f}")
        # H-c: irregular fraction, early vs late hold
        print("H-c  irregular fraction in the reference runs")
        for rin in (0.0, 2.0):
            rs = [r for r in res if r["variant"] == "ref" and r["cfg"][2] == rin]
            a = [pattern(r["log"], 650, 1100) for r in rs]; b = [pattern(r["log"], 1250, 1700) for r in rs]
            irr = lambda ps: sum(p.endswith("~") or p == "none" for p in ps)
            mixed = 0
            for r, p in zip(rs, a):
                if p.endswith("~"):
                    labs = {base(x) for t, x in window_labels(late(r["log"], 650, 1100)) if not x.endswith("~") and x != "none"}
                    mixed += len(labs) > 1
            print(f"  local production {rin:g}: 650-1100 irregular {irr(a)}/{len(rs)} (of which mixtures of regular types: {mixed}); "
                  f"1250-1700 irregular {irr(b)}/{len(rs)};  late outcomes {sorted(set(b))}")
            tally = {}
            for p in b:
                tally[p] = tally.get(p, 0) + 1
            print(f"     1250-1700 outcome counts: {tally}")
