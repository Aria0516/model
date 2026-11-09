"""Is local auxin production in the meristem a switch between decussate and spiral?  See PROTOCOL.md.

python switch.py calib | run | report
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
from t_types import RC_END, RC_START, TRACK, RampSim, calib_job, footprint_job, new_params  # noqa: E402
from model import Sim  # noqa: E402

OUT = HERE / "out"
RINS = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0)
KCS = (1.0, 1.5)
DS = 2.0


def key(rc, kc, rin):
    return f"{rc}|{kc}|{rin}"


def run_job(j):
    kc, rin, start, seed, cal = j
    rho_end, rho_start = cal[key(RC_END, kc, rin)], cal[key(RC_START, kc, rin)]
    common = dict(Th=TH_REL * TARGET_LEVEL, mesh_seed=seed, seed=seed, t_end=1700.0, **TRACK)
    if start == "ramp":
        sim = RampSim(new_params(RC_START, kc, DS, rin, rho_start, **common),
                      dict(T=600.0, rc0=RC_START, rc1=RC_END, rho0=rho_start, rho1=rho_end, ds=DS))
    else:
        sim = Sim(new_params(RC_END, kc, DS, rin, rho_end, **common))
    sim.run()
    out = dict(kc=kc, rin=rin, start=start, seed=seed)
    for name, (t0, t1) in (("early", (650.0, 1100.0)), ("late", (1250.0, 1700.0))):
        sub = [l for l in sim.log if t0 <= l[0] < t1]
        out[name] = analysis.summarize(sub, 0.03, skip=0.0)["pattern"] if len(sub) >= 12 else "none"
    return out


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    if which == "calib":
        jobs = [(rc, kc, DS, rin) for rc in (RC_START, RC_END) for kc in KCS for rin in RINS]
        with Pool(24) as pool:
            res = pool.map(calib_job, jobs)
        json.dump({key(r["rc"], r["kc"], r["rin"]): r["rho_far"] for r in res}, open(OUT / "calib.json", "w"), indent=1)
        json.dump(res, open(OUT / "calib_full.json", "w"), indent=1)
        print("ring        kc    rho_in   rho_far   ring(T=0)/ring   meets R0")
        for r in res:
            print(f"{r['rc']:4.1f}-{r['rc']+2:<4.1f}  {r['kc']:4.1f}  {r['rin']:5.1f}   {r['rho_far']:7.2f}      {r['ratio_T0']:5.2f}          {'yes' if r['ratio_T0'] < TH_REL else 'NO'}")
        # static footprint of one primordium 4 cells outside the ring, final ring
        fj = []
        for kc in KCS:
            for rin in RINS:
                p = new_params(RC_END, kc, DS, rin, json.load(open(OUT / "calib.json"))[key(RC_END, kc, rin)], **TRACK)
                fj += [(f"{kc}|{rin}", p, 4.0, s) for s in (1, 2, 3)]
        with Pool(24) as pool:
            fr = pool.map(footprint_job, fj)
        json.dump(fr, open(OUT / "footprint.json", "w"))
    elif which == "run":
        cal = json.load(open(OUT / "calib.json"))
        jobs = [(kc, rin, "ramp", s, cal) for kc in KCS for rin in RINS for s in range(1, 17)]
        jobs += [(1.0, rin, "direct", s, cal) for rin in RINS for s in range(1, 9)]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "runs.json", "w"))
        print("done", len(res))
    elif which == "report":
        res = json.load(open(OUT / "runs.json"))
        full = {key(r["rc"], r["kc"], r["rin"]): r for r in json.load(open(OUT / "calib_full.json"))}
        fr = json.load(open(OUT / "footprint.json"))
        for period in ("late", "early"):
            print("\n=== period " + ("1250-1700 (main)" if period == "late" else "650-1100"))
            print("start    kc    rho_in  R0 (both ends)  depth@ring+4  runs  spiral  lucas  decussate  distichous  other-regular  irregular")
            for start, kcs in (("ramp", KCS), ("direct", (1.0,))):
                for kc in kcs:
                    for rin in RINS:
                        rs = [r for r in res if r["start"] == start and r["kc"] == kc and r["rin"] == rin]
                        pats = [r[period] for r in rs]
                        c = lambda k: sum(p == k for p in pats)
                        other = sum((not p.endswith("~")) and p not in ("spiral", "lucas", "decussate", "distichous", "none") for p in pats)
                        irr = sum(p.endswith("~") or p == "none" for p in pats)
                        r0 = all(full[key(rc, kc, rin)]["ratio_T0"] < TH_REL for rc in (RC_START, RC_END))
                        depth = np.mean([np.mean(f["prof"][:1]) for f in fr if f["name"] == f"{kc}|{rin}"])
                        print(f"{start:7s}  {kc:4.1f}  {rin:5.1f}   {'yes' if r0 else 'NO ':3s}            {depth:5.2f}       {len(rs):3d}   {c('spiral'):5d}  {c('lucas'):5d}  "
                              f"{c('decussate'):8d}  {c('distichous'):9d}  {other:12d}  {irr:8d}")
        # verdict on the main period (operational definitions: PROTOCOL addendum 2)
        print("\n=== verdict, ramp start, 1250-1700")
        ok = []
        for kc in KCS:
            cnt = lambda rin, k: sum(r["late"] == k for r in res if r["start"] == "ramp" and r["kc"] == kc and r["rin"] == rin)
            n = lambda rin: sum(1 for r in res if r["start"] == "ramp" and r["kc"] == kc and r["rin"] == rin)
            dec0 = cnt(0.0, "decussate") >= 0.5 * n(0.0)
            dec_hi = all(cnt(rin, "decussate") <= 0.1 * n(rin) for rin in RINS if rin >= 2.0)
            sp = [cnt(rin, "spiral") for rin in RINS]
            mono = all(b - a >= -2 for a, b in zip(sp, sp[1:])) and sp[-1] >= sp[0]
            ok.append(dec0 and dec_hi and mono)
            print(f"kc={kc}: decussate at rho_in=0 >= 50%: {dec0}; decussate <= 10% at rho_in >= 2: {dec_hi}; spiral {sp} roughly rising: {mono}")
        print("verdict:", {2: "confirmed", 1: "partial", 0: "not confirmed"}[sum(ok)])
