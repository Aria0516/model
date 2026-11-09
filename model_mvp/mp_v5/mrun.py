"""Step 2 of PROTOCOL.md: phyllotaxis runs for every (n, tau_m) that passed the corrected mechanics check.

python mrun.py run
python mrun.py report
"""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "frozen_v2"))
sys.path.insert(1, str(HERE.parent / "calib_v2"))
sys.path.insert(2, str(HERE))

import numpy as np  # noqa: E402

import analysis  # noqa: E402
import mainline as M  # noqa: E402
import noise_tools  # noqa: E402
import run as C  # noqa: E402
from mp import MPSim  # noqa: E402

GEO = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))
RC, UM = GEO["rc_end"], GEO["um"]
RHO = {(r["rc"], r["rin"]): r["rho_far"] for r in GEO["calib"]}
OUT = HERE / "out"
T0, T1 = 1250.0, 1700.0


def passing():
    """(hill, tau) combinations passing C1-C3 in the corrected mechanics check, for both rho_in."""
    res = json.load(open(OUT / "proto_mp.json"))
    ok = {}
    for r in res:
        if r["T"] is None:
            rf = [row["ring_frac_on"] for row in r["rows"] if row["t"] >= 700]
            pt = [row["ring_patches"] for row in r["rows"] if row["t"] >= 700]
            c1 = bool(rf) and max(rf) < 0.3 and max(pt) >= 1
            ok.setdefault((r["hill"], r["tau"]), []).append(c1 and r["late"] > 0)
    c3 = all(r["events"] == 0 for r in res if r["T"] is not None)
    return [k for k, v in ok.items() if all(v) and c3]


def job(j):
    rin, hill, tau, seed = j
    p = C.geo_params(M.RC_START, rin, RHO[(M.RC_START, rin)], RC, t_end=T1, hill_m=hill, tau_m=tau, mesh_seed=seed, seed=seed)
    sim = MPSim(p, dict(T=M.T_RAMP, rc0=M.RC_START, rc1=RC, rho0=RHO[(M.RC_START, rin)], rho1=RHO[(RC, rin)], ds=M.SRC_OFFSET)).run()
    late = [l for l in sim.log if T0 <= l[0] < T1]
    s = analysis.summarize(late, sim.p["gamma"], skip=0.0) if len(late) >= 12 else dict(pattern="none")
    rs = noise_tools.rank_spread(late, kmax=5, skip=0.0) if len(late) >= 12 else [float("nan")] * 5
    return dict(rin=rin, hill=hill, tau=tau, seed=seed, n=len(late), pattern=s["pattern"], alpha=s.get("alpha"),
                f_alpha=s.get("f_alpha"), gap=s.get("gap_mean"), gap_cv=s.get("gap_cv"), frac_short=s.get("frac_short"),
                G=s.get("G"), spread=float(np.nanmean(rs)),
                r_commit=float(np.median([math.hypot(l[1], l[2]) * UM for l in late])) if late else float("nan"))


if __name__ == "__main__":
    which = sys.argv[1]
    if which == "run":
        combos = passing()
        print("combinations passing C1-C3:", combos, flush=True)
        jobs = [(rin, h, tau, s) for (h, tau) in combos for rin in M.RHO_IN for s in range(1, 17)]
        with Pool(28) as pool:
            res = pool.map(job, jobs)
        json.dump(res, open(OUT / "runs.json", "w"))
        print("done", len(res))
    else:
        res = json.load(open(OUT / "runs.json"))
        base = json.load(open(HERE.parent / "calib_v2" / "out" / "runs.json"))
        print("data: angle 137.5, non-canonical 15%, P1-P5 spread 6.7 deg, interval CV 0.22, G 0.23, P0 radius 29.0 um")
        print("model                      rho_in  regular  patterns                                   angle  non-can  spread  gap CV  clustered  G     r (um)")

        def row(name, rin, rs):
            pats = {}
            for r in rs:
                pats[r["pattern"]] = pats.get(r["pattern"], 0) + 1
            ps = ", ".join(f"{k} {v}" for k, v in sorted(pats.items(), key=lambda x: -x[1]))[:42]
            g = lambda k: float(np.nanmedian([r[k] if r.get(k) is not None else np.nan for r in rs]))
            reg = sum(not r["pattern"].endswith("~") and r["pattern"] != "none" for r in rs)
            print(f"{name:26s} {rin:4.0f}    {reg:3d}/{len(rs):<3d} {ps:42s} {g('alpha'):6.1f}  {100 * (1 - g('f_alpha')):5.0f}%  {g('spread'):5.1f}  "
                  f"{g('gap_cv'):5.2f}   {100 * g('frac_short'):5.1f}%   {g('G'):4.2f}  {g('r_commit'):5.1f}")
            return reg, g("frac_short"), 1 - g("f_alpha"), g("spread"), g("gap_cv")

        for rin in M.RHO_IN:
            row("main line v2 (calibrated)", rin, [r for r in base if r["name"] == "calibrated" and r["rin"] == rin])
        q1 = []
        for (h, tau) in sorted({(r["hill"], r["tau"]) for r in res}):
            for rin in M.RHO_IN:
                reg, fs, nc, sp, cv = row(f"response n {h:.0f} tau_m {tau:.0f}", rin, [r for r in res if r["hill"] == h and r["tau"] == tau and r["rin"] == rin])
                q1.append(((h, tau, rin), reg >= 12, fs <= 0.05, nc, sp, cv))
        full = [x for x in q1 if x[1] and x[2]]
        part = [x for x in q1 if x[1] != x[2]]
        print("\nQ1:", "pass" if full else ("partial" if part else "fail"), "| combinations meeting both:", [x[0] for x in full])
        for (k, a, b, nc, sp, cv) in full:
            closer = sum([abs(nc - 0.15) < 0.15, abs(sp - 6.7) < abs(3.25 - 6.7), abs(cv - 0.22) < abs(0.145 - 0.22)])
            print(f"Q2 {k}: closer to data than the main line on {closer} of 3 (non-canonical, spread, interval CV)")
