"""Structural change 1: auxin is produced in the periphery and reaches the ring by polar transport.

See PROTOCOL.md (written before any run).   python s1_supply.py levels | patterns
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))                    # development model (frozen_v1 is left untouched)

import numpy as np  # noqa: E402

import analysis  # noqa: E402
import noise_tools  # noqa: E402
from e10_phase_sub import OP  # noqa: E402
from model import Sim, pin_vectors  # noqa: E402
from nexp import FIELD  # noqa: E402

OUT = HERE / "out"
RINGS = {"ring 3.5-5.5, w 3": dict(R_c=3.5, w=3.0), "ring 5.5-7.5, w 2": dict(R_c=5.5, w=2.0)}
GRID = [(kc, ds, rin) for kc in (0.5, 1.0, 1.5) for ds in (2.0, 4.0) for rin in (0.0, 2.0)]
TARGET_LEVEL, TH_REL = 4.0, 0.82


def params(ring, kc, ds, rin, rho_far, **extra):
    g = RINGS[ring]
    p = dict(OP, w=g["w"], R_c=g["R_c"], R_p=g["R_c"] + 2.0, R_out=g["R_c"] + 9.0, rho_cz=rin, rho_pz=rin, rho_prox=rin,
             R_src=g["R_c"] + 2.0 + ds, rho_far=rho_far, kappa_c=kc, pin_cz=0.2)
    p.update(extra)
    return p


def relax(sim, t_relax=60.0):
    """Sink-free steady state on the initial tissue (no growth, no primordia)."""
    A = sim.A.copy()
    n = int(t_relax / sim.p["dt"])
    for k in range(n):
        A = sim._step(A)
        if k == n - int(10.0 / sim.p["dt"]):
            A_before = A.copy()
    p, rad, pts = sim.p, sim.rad, sim.tis.pts
    ring = (rad >= p["R_c"]) & (rad < p["R_p"]); cz = rad < p["R_c"]
    mid = (rad >= p["R_p"]) & (rad < p["R_src"])
    pv = pin_vectors(A, sim.G, p)
    inward = -(pv[:, 0] * pts[:, 0] + pv[:, 1] * pts[:, 1]) / np.maximum(rad, 1e-9)
    # variation around the ring after removing the radial trend (a radial gradient is not spontaneous patterning)
    coef = np.polyfit(rad[ring], A[ring], 1)
    cv_az = float((A[ring] - np.polyval(coef, rad[ring])).std() / max(A[ring].mean(), 1e-9))
    return dict(ring=float(A[ring].mean()), ring_cv=float(A[ring].std() / max(A[ring].mean(), 1e-9)), ring_cv_az=cv_az, cz=float(A[cz].mean()),
                far=float(A[rad >= p["R_src"]].mean()), amax=float(A.max()), pin_ring=float(inward[ring].mean()),
                pin_mid=float(inward[mid].mean()), drift=float(abs(A[ring].mean() - A_before[ring].mean())))


def set_rho(sim, rho_far=None, T=None):
    if rho_far is not None:
        sim.p["rho_far"] = rho_far
        sim.G["rho"] = sim._rho(sim.rad)
    if T is not None:
        sim.p["T"] = T


def level_job(job):
    ring, kc, ds, rin = job
    sim = Sim(dict(params(ring, kc, ds, rin, 10.0), Th=1e9, t_end=1.0, init_frac=1.0))
    lo, hi = 0.5, 4000.0
    set_rho(sim, hi)
    top = relax(sim)
    if top["ring"] < TARGET_LEVEL:                       # cannot reach the reference ring level at all
        return dict(ring=ring, kc=kc, ds=ds, rin=rin, rho_far=None, reach=top["ring"])
    for _ in range(14):                                  # bisection on a log scale
        mid = (lo * hi) ** 0.5
        set_rho(sim, mid)
        if relax(sim, 40.0)["ring"] < TARGET_LEVEL:
            lo = mid
        else:
            hi = mid
    rho_far = (lo * hi) ** 0.5
    set_rho(sim, rho_far)
    on = relax(sim)
    set_rho(sim, T=0.0)
    off = relax(sim)
    return dict(ring=ring, kc=kc, ds=ds, rin=rin, rho_far=rho_far, on=on, off=off)


def pattern_job(job):
    ring, kc, ds, rin, rho_far, mode, seed, T, t_end = job
    extra = dict(Th_rel=TH_REL, t_cal=60.0, t_end=t_end, mesh_seed=seed, seed=seed, diag=1)
    if mode == "frozen-style":
        extra.update(FIELD, commit="track", tau_c=2.0)
    p = params(ring, kc, ds, rin, rho_far, **extra)
    if T is not None:                                    # control without polar transport: threshold from the transport-on level
        ref = Sim(dict(p, t_end=1.0))
        p.update(Th_rel=0.0, Th=ref.p["Th"], T=T)
    try:
        sim = Sim(p).run()
    except Exception as e:
        return dict(ring=ring, kc=kc, ds=ds, rin=rin, mode=mode, seed=seed, T=T, pattern="ERROR", error=f"{type(e).__name__}: {e}")
    s = analysis.summarize(sim.log, sim.p["gamma"])
    s.update(ring=ring, kc=kc, ds=ds, rin=rin, mode=mode, seed=seed, T=T, Th=sim.p["Th"], rank=noise_tools.rank_spread(sim.log))
    if sim.dg_n:
        s.update(prof=(sim.dg_prof / sim.dg_n).round(3).tolist(), pin_in_free=(sim.dg_in_free / sim.dg_n).round(3).tolist())
    return s


def recheck_job(job):
    ring, kc, ds, rin, rho_far, seed, start = job
    extra = dict(Th_rel=TH_REL, t_cal=60.0, t_end=600.0, mesh_seed=seed, seed=seed, commit="track", tau_c=2.0, **FIELD)
    if start == "pair":
        extra.update(start="pair", init_frac=1.0)
    sim = Sim(params(ring, kc, ds, rin, rho_far, **extra)).run()
    s = analysis.summarize(sim.log, sim.p["gamma"])
    th = np.degrees(np.arctan2([l[2] for l in sim.log], [l[1] for l in sim.log])) % 360
    d = np.diff(th) % 360
    k = len(d) // 3
    ccw = bool((d[k:] < 180).mean() >= 0.5) if len(d) > 9 else None
    return dict(ring=ring, kc=kc, ds=ds, rin=rin, seed=seed, start=start, ccw=ccw, pattern=s["pattern"], Rb_sd=s.get("Rb_sd"))


def lab(r):
    return f"kc={r['kc']:g} src=+{r['ds']:g} rho_in={r['rin']:g}"


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    if which == "levels":
        jobs = [(ring, kc, ds, rin) for ring in RINGS for (kc, ds, rin) in GRID]
        with Pool(24) as pool:
            res = pool.map(level_job, jobs)
        json.dump(res, open(OUT / "levels.json", "w"), indent=1)
        for ring in RINGS:
            print(f"\n=== {ring}   (sink-free state; ring level set to {TARGET_LEVEL} with transport on)")
            print("config                         rho_far   ring(T=0)  ratio   R0     ring CV  R1   azimuthal CV  R1'   central zone  far zone  PIN inward: ring / ring..source")
            for r in res:
                if r["ring"] != ring:
                    continue
                if r["rho_far"] is None:
                    print(f"{lab(r):30s} cannot reach the reference level (ring = {r['reach']:.2f} at the largest source)"); continue
                on, off = r["on"], r["off"]
                ratio = off["ring"] / on["ring"]
                print(f"{lab(r):30s} {r['rho_far']:7.1f}   {off['ring']:6.2f}    {ratio:5.2f}  {'ok ' if ratio < TH_REL else 'NO '}    "
                      f"{on['ring_cv']:5.2f}   {'ok ' if on['ring_cv'] <= 0.10 else 'NO '}    {on['ring_cv_az']:5.2f}     {'ok ' if on['ring_cv_az'] <= 0.10 else 'NO '}    "
                      f"{on['cz']:6.2f}       {on['far']:6.2f}      "
                      f"{on['pin_ring']:+.2f} / {on['pin_mid']:+.2f}   (drift {on['drift']:.3f})")
    elif which == "recheck":
        # P5: the three held-out tests the frozen model passed, on the new structure (ring 5.5-7.5, frozen-style, all 9 configurations)
        import math
        lev = json.load(open(OUT / "levels.json"))
        ok = [r for r in lev if r["ring"].startswith("ring 5.5") and r["rho_far"] is not None
              and r["off"]["ring"] / r["on"]["ring"] < TH_REL and r["on"]["ring_cv_az"] <= 0.10]
        jobs = [(r["ring"], r["kc"], r["ds"], r["rin"], r["rho_far"], s, "noise") for r in ok for s in range(1, 9)]
        jobs += [(r["ring"], r["kc"], r["ds"], r["rin"], r["rho_far"], s, "pair") for r in ok for s in range(1, 5)]
        with Pool(28) as pool:
            res = pool.map(recheck_job, jobs)
        json.dump(res, open(OUT / "recheck.json", "w"))
        a = [x for x in res if x["start"] == "noise" and x["ccw"] is not None]
        k, n = sum(x["ccw"] for x in a), len(a)
        pval = sum(math.comb(n, i) for i in range(n + 1) if abs(i - n / 2) >= abs(k - n / 2)) / 2 ** n
        print(f"handedness over {len(ok)} configurations x 8 seeds: {k} counter-clockwise, {n - k} clockwise; two-sided binomial p = {pval:.2f}")
        b = [x for x in res if x["start"] == "pair"]
        cnt = {}
        for x in b:
            cnt[x["pattern"]] = cnt.get(x["pattern"], 0) + 1
        reg = sum(not x["pattern"].endswith("~") for x in b)
        print(f"opposite-pair start, {len(b)} runs: regular {reg}/{len(b)}; of these spiral or Lucas {sum(x['pattern'] in ('spiral', 'lucas') for x in b)}; patterns {cnt}")
        rb = [x["Rb_sd"] for x in res if x["Rb_sd"] is not None]
        print(f"initiation radius spread: mean {np.mean(rb):.2f} cells (max {np.max(rb):.2f})")
    elif which == "patterns":
        lev = json.load(open(OUT / "levels.json"))
        ok = [r for r in lev if r["rho_far"] is not None and r["off"]["ring"] / r["on"]["ring"] < TH_REL and r["on"]["ring_cv_az"] <= 0.10]
        strict = sum(r["on"]["ring_cv"] <= 0.10 for r in ok)
        print(f"{len(ok)} of {len(lev)} configurations meet R0 and the amended R1 and enter the pattern runs "
              f"({strict} of them also meet R1 as first written)")
        jobs = []
        for r in ok:
            for mode in ("plain", "frozen-style"):
                jobs += [(r["ring"], r["kc"], r["ds"], r["rin"], r["rho_far"], mode, s, None, 600.0) for s in range(1, 9)]
            jobs += [(r["ring"], r["kc"], r["ds"], r["rin"], r["rho_far"], "plain", s, 0.0, 300.0) for s in range(1, 4)]
        with Pool(28) as pool:
            res = pool.map(pattern_job, jobs)
        json.dump(res, open(OUT / "patterns.json", "w"))
        for ring in RINGS:
            for mode in ("plain", "frozen-style"):
                print(f"\n=== {ring} | {mode}")
                print("config                          G    angle  non-canon  intervalCV  regular  spread1-5   CZ/ring  PIN ring  | no transport: primordia  | patterns")
                for r0 in ok:
                    if r0["ring"] != ring:
                        continue
                    sel = lambda T: [x for x in res if x["ring"] == ring and x["mode"] == (mode if T is None else "plain") and x["T"] == T
                                     and (x["kc"], x["ds"], x["rin"]) == (r0["kc"], r0["ds"], r0["rin"])]
                    rs_all, ctl = sel(None), sel(0.0)
                    nT0 = [x.get("n", 0) for x in ctl]
                    rs = [x for x in rs_all if x["pattern"] not in ("ERROR", "none")]
                    if not rs:
                        err = [x.get("error") for x in rs_all if x["pattern"] == "ERROR"]
                        print(f"{lab(r0):30s} no primordia in {len(rs_all)} runs {err[:1] if err else ''}   | {nT0}"); continue
                    g = lambda k: float(np.mean([x[k] for x in rs]))
                    reg = sum(not x["pattern"].endswith("~") for x in rs)
                    clean = [x for x in rs if x.get("jugacy", 9) <= 1 and x["f_perm"] == 0 and x["f_other"] <= 0.03]
                    sp = f"{np.nanmean([np.nanmean(x['rank'][:5]) for x in clean]):5.1f}" if clean else "   --"
                    prof = np.mean([x["prof"] for x in rs if "prof" in x], axis=0); pin = np.mean([x["pin_in_free"] for x in rs if "pin_in_free" in x], axis=0)
                    rc = int(RINGS[ring]["R_c"]); czr = prof[:rc].mean() / prof[rc + 1:rc + 3].mean(); pinr = pin[rc + 1:rc + 3].mean()
                    pats = {}
                    for x in rs:
                        pats[x["pattern"]] = pats.get(x["pattern"], 0) + 1
                    print(f"{lab(r0):30s} {0.03*g('gap_mean'):4.2f}  {np.median([x['alpha'] for x in rs]):6.1f}   {100*(1-g('f_alpha')):5.0f}%     {g('gap_cv'):5.2f}     "
                          f"{reg}/{len(rs_all)}     {sp}       {czr:5.2f}    {pinr:+.2f}    | {nT0}   | {pats}")
