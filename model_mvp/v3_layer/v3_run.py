"""Structural change 2 (inner layer): calibration, runs and report.  See PROTOCOL.md.

python v3_run.py calib | run | report
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for d in (ROOT, ROOT / "v2_supply", ROOT / "v2_supply" / "why_types", HERE):
    sys.path.insert(0, str(d))

import numpy as np  # noqa: E402

import analysis  # noqa: E402
from layer import TwoLayerSim  # noqa: E402
from model import Sim  # noqa: E402
from s1_supply import TARGET_LEVEL, TH_REL, set_rho  # noqa: E402
from t_types import RC_END, RC_START, TRACK, RampSim, new_params  # noqa: E402

OUT = HERE / "out"
KC, DS = 1.0, 2.0
RINS = (0.0, 2.0)
KVS = (0.3, 1.0)
KES = (0.0, 3.0)           # 0 = linear transfer
ETA2S = (1.0, 3.0)
TH = TH_REL * TARGET_LEVEL
READOUT = dict(tau_R=15.0, theta_M=3.0, track=1)


def relax2(sim, t=60.0):
    sim.A2 = np.zeros(sim.tis.n)
    A = sim.A.copy()
    for _ in range(int(t / sim.p["dt"])):
        A = sim._step(A)
    ring = (sim.rad >= sim.p["R_c"]) & (sim.rad < sim.p["R_p"])
    return float(A[ring].mean())


def calib_job(job):
    rc, rin, kv = job
    sim = TwoLayerSim(dict(new_params(rc, KC, DS, rin, 10.0), Th=1e9, t_end=1.0, init_frac=1.0, k_v=kv))
    lo, hi = 0.2, 4000.0
    for _ in range(15):
        mid = (lo * hi) ** 0.5
        set_rho(sim, mid)
        if relax2(sim, 40.0) < TARGET_LEVEL:
            lo = mid
        else:
            hi = mid
    rho = (lo * hi) ** 0.5
    set_rho(sim, rho)
    on = relax2(sim)
    set_rho(sim, T=0.0)
    off = relax2(sim)
    return dict(rc=rc, rin=rin, kv=kv, rho_far=rho, ring=on, ratio_T0=off / on)


def ckey(rc, rin, kv):
    return f"{rc}|{rin}|{kv}"


def traces(sim, t0, t1, gap):
    """Per primordium committed in [t0, t1]: time its centre stays above threshold, and read-out onset."""
    above, onset, n_on, n = [], [], 0, 0
    for pid, tr in sim.track.items():
        tr = np.array(tr)                                  # t, r, A, M, R
        tc = tr[0, 0]
        if not (t0 <= tc <= t1) or len(tr) < 20:
            continue
        n += 1
        a = tr[:, 2]
        below = np.where(a < TH)[0]
        above.append(((tr[below[0], 0] if len(below) else tr[-1, 0]) - tc) / gap)
        on = np.where(tr[:, 4] >= 0.5)[0]
        if len(on):
            n_on += 1
            onset.append((tr[on[0], 0] - tc) / gap)
    return above, onset, n_on, n


def run_job(job):
    kind, rin, kv, ke, eta2, seed, T, cal = job
    if kind == "single":
        rho_s, rho_e = cal["single"][f"{RC_START}|{rin}"], cal["single"][f"{RC_END}|{rin}"]
    else:
        rho_s, rho_e = cal["layer"][ckey(RC_START, rin, kv)], cal["layer"][ckey(RC_END, rin, kv)]
    common = dict(Th=TH, mesh_seed=seed, seed=seed, **TRACK, **READOUT)
    if T is not None:                                      # control without polar transport at the final geometry
        p = new_params(RC_END, KC, DS, rin, rho_e, t_end=300.0, T=T, **common)
        sim = (Sim(p) if kind == "single" else TwoLayerSim(dict(p, k_v=kv, K_e=ke, eta2=eta2))).run()
        return dict(kind=kind, rin=rin, kv=kv, ke=ke, eta2=eta2, seed=seed, T=T, n=len(sim.log))
    p = new_params(RC_START, KC, DS, rin, rho_s, t_end=1700.0, **common)
    ramp = dict(T=600.0, rc0=RC_START, rc1=RC_END, rho0=rho_s, rho1=rho_e, ds=DS)
    sim = (RampSim(p, ramp) if kind == "single" else TwoLayerSim(dict(p, k_v=kv, K_e=ke, eta2=eta2), ramp)).run()
    late = [l for l in sim.log if 1250.0 <= l[0] < 1700.0]
    s = analysis.summarize(late, 0.03, skip=0.0) if len(late) >= 12 else dict(pattern="none")
    gap = float(np.mean(np.diff([l[0] for l in late]))) if len(late) > 3 else float("nan")
    above, onset, n_on, n = traces(sim, 1250.0, 1550.0, gap)
    return dict(kind=kind, rin=rin, kv=kv, ke=ke, eta2=eta2, seed=seed, T=None, pattern=s["pattern"], alpha=s.get("alpha"),
                gap=gap, above=above, onset=onset, n_on=n_on, n_prim=n)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    if which == "calib":
        jobs = [(rc, rin, kv) for rc in (RC_START, RC_END) for rin in RINS for kv in KVS]
        with Pool(8) as pool:
            res = pool.map(calib_job, jobs)
        single = json.load(open(ROOT / "v2_supply" / "why_types" / "out" / "calib.json"))
        cal = dict(layer={ckey(r["rc"], r["rin"], r["kv"]): r["rho_far"] for r in res},
                   single={f"{rc}|{rin}": single[f"{rc}|{DS}|{rin}"] for rc in (RC_START, RC_END) for rin in RINS})
        json.dump(cal, open(OUT / "calib.json", "w"), indent=1)
        print("ring        rho_in  k_v   rho_far   free ring level   ring(T=0)/ring   meets R0")
        for r in res:
            print(f"{r['rc']:4.1f}-{r['rc']+2:<4.1f}  {r['rin']:5.1f}  {r['kv']:4.1f}  {r['rho_far']:7.2f}      {r['ring']:5.2f}            {r['ratio_T0']:5.2f}          "
                  f"{'yes' if r['ratio_T0'] < TH_REL else 'NO'}")
    elif which == "run":
        cal = json.load(open(OUT / "calib.json"))
        jobs = [("layer", rin, kv, ke, e2, s, None, cal) for rin in RINS for kv in KVS for ke in KES for e2 in ETA2S for s in range(1, 9)]
        jobs += [("single", rin, None, None, None, s, None, cal) for rin in RINS for s in range(1, 9)]
        jobs += [("layer", rin, kv, ke, e2, s, 0.0, cal) for rin in RINS for kv in KVS for ke in KES for e2 in ETA2S for s in range(1, 4)]
        jobs += [("single", rin, None, None, None, s, 0.0, cal) for rin in RINS for s in range(1, 4)]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "runs.json", "w"))
        print("done", len(res))
    elif which == "report":
        res = json.load(open(OUT / "runs.json"))
        print("main period 1250-1700; durations in units of the mean interval between primordia")
        print("model                          rho_in  runs  patterns                                   above-threshold median   read-out on   onset median   no transport: primordia")
        groups = [("single", rin, None, None, None) for rin in RINS]
        groups += [("layer", rin, kv, ke, e2) for rin in RINS for kv in KVS for ke in KES for e2 in ETA2S]
        stats = {}
        for kind, rin, kv, ke, e2 in groups:
            sel = lambda T: [r for r in res if r["kind"] == kind and r["rin"] == rin and r["T"] == T and r["kv"] == kv and r["ke"] == ke and r["eta2"] == e2]
            rs, ctl = sel(None), sel(0.0)
            pats = {}
            for r in rs:
                pats[r["pattern"]] = pats.get(r["pattern"], 0) + 1
            above = sum((r["above"] for r in rs), [])
            onset = sum((r["onset"] for r in rs), [])
            n_on = sum(r["n_on"] for r in rs); n = sum(r["n_prim"] for r in rs)
            name = "single layer" if kind == "single" else f"k_v={kv:g} K_e={'inf' if ke == 0 else ke:} eta2={e2:g}"
            ps = ", ".join(f"{k} {v}" for k, v in sorted(pats.items(), key=lambda kv_: -kv_[1]))
            print(f"{name:30s} {rin:5.1f}   {len(rs):3d}   {ps:42s}  {np.median(above) if above else float('nan'):6.2f}               "
                  f"{n_on:4d}/{n:<4d}     {np.median(onset) if onset else float('nan'):6.2f}         {[r['n'] for r in ctl]}")
            stats[(kind, rin, kv, ke, e2)] = dict(above=np.median(above) if above else np.nan, frac_on=n_on / max(n, 1),
                                                  onset=np.median(onset) if onset else np.nan, ctl=[r["n"] for r in ctl])
        lay = {k: v for k, v in stats.items() if k[0] == "layer"}
        longer = all(v["above"] > stats[("single", k[1], None, None, None)]["above"] for k, v in lay.items())
        reach = [k for k, v in lay.items() if v["above"] >= 1.0]
        print("\nPL1 every group longer than single layer:", longer, "| groups with median >= 1 interval:", reach,
              "->", "pass" if longer and reach else ("partial" if longer or reach else "fail"))
        pl2 = [k for k, v in lay.items() if v["frac_on"] > 0.5 and 0.5 <= v["onset"] <= 1.5]
        print("PL2 groups with >50% opening and onset 0.5-1.5 intervals:", pl2, "->", "pass" if pl2 else "fail")
        bad = {k: v["ctl"] for k, v in stats.items() if any(c > 0 for c in v["ctl"])}
        print("PL3 groups producing primordia without polar transport:", bad or "none", "->", "fail" if bad else "pass")
