"""Why is the pattern type indeterminate in the transport-fed structure?  See PROTOCOL.md.

python t_types.py footprint | calib | run | report
"""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402

import analysis  # noqa: E402
from e10_phase_sub import OP  # noqa: E402
from model import Sim  # noqa: E402
from nexp import ARABIDOPSIS_LIKE, FIELD  # noqa: E402
from s1_supply import TARGET_LEVEL, TH_REL, relax, set_rho  # noqa: E402

OUT = HERE / "out"
CONFIGS = [(1.0, ds, rin) for ds in (2.0, 4.0) for rin in (0.0, 2.0)]      # kappa_c, source offset, local production
RC_END, RC_START, W = 5.5, 2.0, 2.0
TRACK = dict(commit="track", tau_c=2.0, **FIELD)


def new_params(rc, kc, ds, rin, rho_far, **extra):
    p = dict(OP, w=W, R_c=rc, R_p=rc + 2.0, R_out=RC_END + 9.0, rho_cz=rin, rho_pz=rin, rho_prox=rin,
             R_src=rc + 2.0 + ds, rho_far=rho_far, kappa_c=kc, pin_cz=0.2)
    p.update(extra)
    return p


def lab(c):
    return f"src=+{c[1]:g} rho_in={c[2]:g}"


# ---- calibration of the peripheral production at both ends of the ramp -------------------------
def calib_job(job):
    rc, kc, ds, rin = job
    sim = Sim(dict(new_params(rc, kc, ds, rin, 10.0), Th=1e9, t_end=1.0, init_frac=1.0))
    lo, hi = 0.2, 4000.0
    for _ in range(15):
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
    return dict(rc=rc, kc=kc, ds=ds, rin=rin, rho_far=rho_far, ring=on["ring"], ratio_T0=off["ring"] / on["ring"], cv_az=on["ring_cv_az"])


# ---- T1: footprint of one primordium on the ring ---------------------------------------------
def footprint_job(job):
    name, p, dr, seed = job
    sim = Sim(dict(p, Th=1e9, t_end=1.0, init_frac=1.0, mesh_seed=seed, seed=seed))
    A = sim.A.copy()
    for _ in range(6000):
        A = sim._step(A)
    free = A.copy()
    rg = 0.5 * (sim.p["R_c"] + sim.p["R_p"])
    sim._add_primordium(rg + dr, 0.0)
    sim.prim[-1]["tc"] = sim.prim[-1]["t0"] = -1e3            # old enough that the secondary field has decayed
    sim.p["start"] = "seeded"
    sim._geometry(first=True)
    for _ in range(6000):
        A = sim._step(A)
    rad, pts = sim.rad, sim.tis.pts
    ring = (rad >= sim.p["R_c"]) & (rad < sim.p["R_p"])
    th = np.abs(np.degrees(np.arctan2(pts[ring, 1], pts[ring, 0])))
    deficit = 1.0 - A[ring] / free[ring]
    bins = np.arange(0, 181, 15)
    prof = [float(deficit[(th >= lo) & (th < hi)].mean()) for lo, hi in zip(bins[:-1], bins[1:])]
    return dict(name=name, dr=dr, seed=seed, prof=prof)


# ---- simulations with different starts ---------------------------------------------------------
class RampSim(Sim):
    """Ring radius (and the peripheral production that keeps the free ring level fixed) changes in time."""

    def __init__(self, params, ramp):
        self._ramp = ramp                                   # dict(T, rc0, rc1, rho0, rho1, ds)
        super().__init__(params)

    def _geometry(self, first=False):
        r = self._ramp
        f = min(max(self.t / r["T"], 0.0), 1.0)
        rc = r["rc0"] + f * (r["rc1"] - r["rc0"])
        self.p.update(R_c=rc, R_p=rc + 2.0, R_src=rc + 2.0 + r["ds"], rho_far=r["rho0"] + f * (r["rho1"] - r["rho0"]))
        super()._geometry(first)


LATTICE = {"spiral": (137.5, 1), "lucas": (99.5, 1), "decussate": (90.0, 2)}


def seeded(params, kind, G=0.31, gamma=0.03):
    """Start from a few primordia arranged as one pattern type, chemistry relaxed, then evolve freely."""
    sim = Sim(dict(params, start="seeded"))
    rg = 0.5 * (sim.p["R_c"] + sim.p["R_p"])
    alpha, jug = LATTICE[kind]
    for k in range(4):
        r = rg * math.exp(G * jug * k + 0.05)
        for m in range(jug):
            a = math.radians(-k * alpha + m * 360.0 / jug)
            q = sim._add_primordium(r * math.cos(a), r * math.sin(a))
            q["t0"] = q["tc"] = -(G * jug * k + 0.05) / gamma
    sim._geometry(first=True)
    for _ in range(3000):                                   # chemistry settles around the seeded primordia before growth starts
        sim.A = sim._step(sim.A)
    sim.M = sim.A.copy()
    sim.p["start"] = "noise"
    return sim


def windows(log, t_from, size=14, step=7):
    """Pattern label of consecutive windows of primordia born after t_from."""
    sub = [l for l in log if l[0] >= t_from]
    labs = []
    for i in range(0, max(len(sub) - size + 1, 0), step):
        s = analysis.summarize(sub[i:i + size], 0.03, skip=0.0)
        labs.append(s["pattern"])
    return labs


def run_job(job):
    cfg, cond, seed, cal = job
    kc, ds, rin = cfg
    rho_end, rho_start = cal[f"{RC_END}|{ds}|{rin}"], cal[f"{RC_START}|{ds}|{rin}"]
    th = TH_REL * TARGET_LEVEL
    common = dict(Th=th, mesh_seed=seed, seed=seed, **TRACK)
    if cond == "direct":
        sim = Sim(new_params(RC_END, kc, ds, rin, rho_end, t_end=900.0, **common)); t_from = 300.0
    elif cond == "ramp":
        sim = RampSim(new_params(RC_START, kc, ds, rin, rho_start, t_end=1100.0, **common),
                      dict(T=600.0, rc0=RC_START, rc1=RC_END, rho0=rho_start, rho1=rho_end, ds=ds)); t_from = 650.0
    else:
        sim = seeded(new_params(RC_END, kc, ds, rin, rho_end, t_end=600.0, **common), cond); t_from = 200.0
    sim.run()
    late = [l for l in sim.log if l[0] >= t_from]
    s = analysis.summarize(late, 0.03, skip=0.0)
    return dict(cfg=list(cfg), cond=cond, seed=seed, pattern=s["pattern"], alpha=s.get("alpha"), jug=s.get("jugacy"), G=s.get("G"),
                f_alpha=s.get("f_alpha"), n=len(late), win=windows(sim.log, t_from))


def base(pat):
    return pat.rstrip("~")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    if which == "calib":
        jobs = [(rc, kc, ds, rin) for rc in (RC_START, RC_END) for (kc, ds, rin) in CONFIGS]
        with Pool(8) as pool:
            res = pool.map(calib_job, jobs)
        json.dump({f"{r['rc']}|{r['ds']}|{r['rin']}": r["rho_far"] for r in res}, open(OUT / "calib.json", "w"), indent=1)
        print("ring start   config               rho_far   free ring level   ring(T=0)/ring   azimuthal CV")
        for r in res:
            print(f"{r['rc']:4.1f}-{r['rc']+2:<4.1f}   {lab((r['kc'], r['ds'], r['rin'])):18s} {r['rho_far']:8.2f}      {r['ring']:5.2f}            {r['ratio_T0']:5.2f}          {r['cv_az']:.2f}")
    elif which == "footprint":
        cal = json.load(open(OUT / "calib.json"))
        models = {"frozen": dict(ARABIDOPSIS_LIKE)}
        for (kc, ds, rin) in CONFIGS:
            models[f"new {lab((kc, ds, rin))}"] = new_params(RC_END, kc, ds, rin, cal[f"{RC_END}|{ds}|{rin}"], **TRACK)
        jobs = [(n, p, dr, s) for n, p in models.items() for dr in (0.0, 2.0, 4.0, 6.0) for s in (1, 2, 3, 4)]
        with Pool(28) as pool:
            res = pool.map(footprint_job, jobs)
        json.dump(res, open(OUT / "footprint.json", "w"))
        print("fraction by which one primordium lowers ring auxin, by azimuthal distance from it (deg); mean of 4 meshes")
        print("model                      primordium at     0-15  15-30  30-45  45-60  60-75  75-90  90-105 105-120 120-135 135-150 150-165 165-180")
        for n in models:
            for dr in (0.0, 2.0, 4.0, 6.0):
                pr = np.mean([r["prof"] for r in res if r["name"] == n and r["dr"] == dr], axis=0)
                print(f"{n:26s} ring+{dr:g} cells    " + "  ".join(f"{v:5.2f}" for v in pr))
    elif which == "run":
        cal = json.load(open(OUT / "calib.json"))
        jobs = []
        for cfg in CONFIGS:
            jobs += [(cfg, "direct", s, cal) for s in range(1, 17)] + [(cfg, "ramp", s, cal) for s in range(1, 17)]
            for kind in LATTICE:
                jobs += [(cfg, kind, s, cal) for s in range(1, 9)]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "runs.json", "w"))
        print("done", len(res))
    elif which == "report":
        res = json.load(open(OUT / "runs.json"))
        kinds = ["spiral", "lucas", "decussate", "distichous", "intermediate"]

        def tally(rs):
            c = {k: 0 for k in kinds}; c["other regular"] = 0; c["irregular"] = 0
            for r in rs:
                if r["pattern"].endswith("~") or r["pattern"] == "none":
                    c["irregular"] += 1
                elif r["pattern"] in c:
                    c[r["pattern"]] += 1
                else:
                    c["other regular"] += 1
            return c

        print("outcome in the analysed period, by start (counts)")
        print("config               start       runs  spiral  lucas  decussate  distichous  intermediate  other-regular  irregular")
        for cfg in CONFIGS + ["ALL"]:
            for cond in ("direct", "ramp", "spiral", "lucas", "decussate"):
                rs = [r for r in res if r["cond"] == cond and (cfg == "ALL" or tuple(r["cfg"]) == cfg)]
                c = tally(rs)
                name = "all four" if cfg == "ALL" else lab(cfg)
                print(f"{name:20s} {cond:10s} {len(rs):4d}  {c['spiral']:5d}  {c['lucas']:5d}  {c['decussate']:8d}  {c['distichous']:9d}  "
                      f"{c['intermediate']:11d}  {c['other regular']:12d}  {c['irregular']:9d}")
        # T2a: do regular runs keep their type through the analysed period?
        dr = [r for r in res if r["cond"] == "direct"]
        reg = [r for r in dr if not r["pattern"].endswith("~") and r["pattern"] != "none"]
        changed = 0
        for r in reg:
            w = [base(x) for x in r["win"] if not x.endswith("~") and x != "none"]
            if len(set(w)) > 1:
                changed += 1
        print(f"\nT2a  direct start: regular runs {len(reg)}/{len(dr)}; of these, runs whose windows show more than one regular type: {changed}")
        irr = [r for r in dr if r["pattern"].endswith("~")]
        mix = sum(len({base(x) for x in r["win"] if not x.endswith("~") and x != "none"}) > 1 for r in irr)
        some = sum(any(not x.endswith("~") and x != "none" for x in r["win"]) for r in irr)
        print(f"     irregular runs {len(irr)}: {some} contain at least one regular window; {mix} contain regular windows of more than one type")
        print("T2b  seeded starts keeping their own type:")
        for kind in ("spiral", "lucas", "decussate"):
            rs = [r for r in res if r["cond"] == kind]
            print(f"     {kind:10s} {sum(r['pattern'] == kind for r in rs)}/{len(rs)}   (end patterns: {tally(rs)})")
        d, m = tally(dr), tally([r for r in res if r["cond"] == "ramp"])
        nd, nm = len(dr), len([r for r in res if r["cond"] == "ramp"])
        print(f"T3   ordinary spiral: direct {d['spiral']}/{nd} = {100*d['spiral']/nd:.0f}%, ramp {m['spiral']}/{nm} = {100*m['spiral']/nm:.0f}%;  "
              f"Lucas: direct {100*d['lucas']/nd:.0f}%, ramp {100*m['lucas']/nm:.0f}%")
