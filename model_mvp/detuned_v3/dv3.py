"""Driver for detuned_v3/PROTOCOL.md: sample, calibrate, run, report. Uses only frozen_v3.

python dv3.py sample      # 120 Latin-hypercube samples -> out/samples.json
python dv3.py calib       # rho_far at the start and end ring for every sample (sink-free rule) + R0
python dv3.py run         # 2 seeds per sample (ramp start, to 1700) + one T = 0 control per sample
python dv3.py report
"""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "frozen_v3"))

import numpy as np  # noqa: E402

import analysis  # noqa: E402
import mainline_v3 as V  # noqa: E402
import noise_tools  # noqa: E402
from layer import TwoLayerSim  # noqa: E402

OUT = HERE / "out"
GEO = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))
RC_END, UM = GEO["rc_end"], GEO["um"]
N, SEEDS, T0, T1 = 120, (1, 2), 1250.0, 1700.0
# (name, low, high, log) -- PROTOCOL section 2
SPACE = [("tau_M", 1.3, 3.2, False), ("theta_rel", 0.65, 0.95, False), ("w", 1.5, 3.0, False), ("eta", 1.5, 6.0, True),
         ("A_q", 4.0, 12.0, False), ("ring_w", 1.5, 3.0, False), ("kappa_c", 0.75, 1.5, False), ("k_v", 0.1, 1.0, True),
         ("K_e", 1.0, 10.0, True), ("eta2", 1.0, 5.0, False), ("rho_in", 0.0, 2.0, False), ("k_rel", 0.0, 0.6, False),
         ("w_I", 2.5, 5.0, False), ("a_on", 7.5, 15.0, False), ("a_off", 22.0, 38.0, False)]
BANDS = dict(alpha=(135, 140), nc=(0.09, 0.21), spread=(4.0, 9.4), gap_cv=(0.13, 0.31), hours=(10, 14), G=(0.18, 0.28), r_um=(26, 33))


def ring_level(sim, t=40.0):
    sim.A2 = np.zeros(sim.tis.n)
    A = sim.A.copy()
    for _ in range(int(t / sim.p["dt"])):
        A = sim._step(A)
    ring = (sim.rad >= sim.p["R_c"]) & (sim.rad < sim.p["R_p"])
    return float(A[ring].mean())


def calib_job(job):
    i, s, rc = job
    sim = TwoLayerSim(V.params(rc, RC_END, s["rho_in"], 10.0, s, Th=1e9, t_end=1.0, init_frac=1.0))
    lo, hi = 0.05, 4000.0
    for _ in range(16):
        mid = (lo * hi) ** 0.5
        sim.p["rho_far"] = mid
        sim.G["rho"] = sim._rho(sim.rad)
        if ring_level(sim) < V.A_FREE:
            lo = mid
        else:
            hi = mid
    rho = (lo * hi) ** 0.5
    sim.p["rho_far"] = rho
    sim.G["rho"] = sim._rho(sim.rad)
    on = ring_level(sim, 60.0)
    sim.p["T"] = 0.0
    off = ring_level(sim, 60.0)
    return dict(i=i, rc=rc, rho_far=rho, ring=on, ratio_T0=off / max(on, 1e-9))


def run_job(job):
    i, s, cal, seed, T = job
    if T is not None:
        sim = V.make(s, s["rho_in"], RC_END, cal["start"], cal["end"], seed, t_end=300.0, ramp=False, T=T).run()
        return dict(i=i, seed=seed, T=T, n=len(sim.log))
    sim = V.make(s, s["rho_in"], RC_END, cal["start"], cal["end"], seed).run()
    late = [l for l in sim.log if T0 <= l[0] < T1]
    out = dict(i=i, seed=seed, T=None, n=len(late))
    if len(late) < 12:
        out.update(pattern="stalled" if len(late) < 3 else "none")
        return out
    sm = analysis.summarize(late, sim.p["gamma"], skip=0.0)
    gaps = np.diff([l[0] for l in late])
    rs = noise_tools.rank_spread(late, kmax=5, skip=0.0)
    out.update(pattern=sm["pattern"], alpha=sm.get("alpha"), nc=1 - sm.get("f_alpha", np.nan), spread=float(np.nanmean(rs)),
               gap_cv=sm.get("gap_cv"), co25=float((gaps < 0.25 * gaps.mean()).mean()), co50=float((gaps < 0.5 * gaps.mean()).mean()),
               hours=float(gaps.mean() * V.HOURS_PER_UNIT), G=sm.get("G"),
               r_um=float(np.median([math.hypot(l[1], l[2]) * UM for l in late])))
    return out


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    if which == "sample":
        from scipy.stats import qmc
        u = qmc.LatinHypercube(d=len(SPACE), seed=20261019).random(N)
        samples = []
        for row in u:
            s = {}
            for (name, lo, hi, log), x in zip(SPACE, row):
                s[name] = float(math.exp(math.log(lo) + x * (math.log(hi) - math.log(lo))) if log else lo + x * (hi - lo))
            samples.append(s)
        json.dump(samples, open(OUT / "samples.json", "w"), indent=1)
        print("samples", len(samples))
    elif which == "calib":
        samples = json.load(open(OUT / "samples.json"))
        jobs = [(i, s, rc) for i, s in enumerate(samples) for rc in (V.RC_START, RC_END)]
        with Pool(28) as pool:
            res = pool.map(calib_job, jobs)
        cal = {}
        for r in res:
            c = cal.setdefault(r["i"], {})
            c["start" if r["rc"] == V.RC_START else "end"] = r["rho_far"]
            if r["rc"] == RC_END:
                c["ratio_T0"], c["ring_end"] = r["ratio_T0"], r["ring"]
        json.dump({str(k): v for k, v in cal.items()}, open(OUT / "calib.json", "w"), indent=1)
        r0 = sum(cal[i]["ratio_T0"] < samples[i]["theta_rel"] for i in cal)
        print(f"calibrated {len(cal)} samples; R0 (ring without transport below threshold) holds in {r0}")
    elif which == "run":
        samples = json.load(open(OUT / "samples.json"))
        cal = {int(k): v for k, v in json.load(open(OUT / "calib.json")).items()}
        jobs = [(i, s, cal[i], seed, None) for i, s in enumerate(samples) for seed in SEEDS]
        jobs += [(i, s, cal[i], 1, 0.0) for i, s in enumerate(samples)]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "runs.json", "w"))
        print("done", len(res))
