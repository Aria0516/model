"""Structural change 3 (PROTOCOL.md).

python nrun.py data      # s_data from the 21 meristems
python nrun.py calib     # sigma* for rho_in 0 and 2 (bisection on s only)
python nrun.py run       # sigma in {0, sigma*/2, sigma*} x rho_in {0, 2} x 16 seeds, plus T = 0 controls
python nrun.py report
python nrun.py dose      # revision 1: sigma in {0, 0.25, 0.5, 1.0} x rho_in {0, 2} x 16 seeds, T = 0 controls at 1.0
python nrun.py dose_report
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
import pandas as pd  # noqa: E402

import analysis  # noqa: E402
import mainline as M  # noqa: E402
import noise_tools  # noqa: E402
import run as C  # noqa: E402   calib_v2/run.py: geo_params
from noise import NoisySim, residual_sd, s_from  # noqa: E402

OUT = HERE / "out"
DATA = HERE.parents[1] / "reproductions" / "elife55832" / "outputs" / "nuclei_21"
GEO = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))
UM, RC = GEO["um"], GEO["rc_end"]
RHO = {(r["rc"], r["rin"]): r["rho_far"] for r in GEO["calib"]}
T0, T1 = 1250.0, 1700.0
DOSE = (0.0, 0.25, 0.5, 1.0)
FINE = (0.3, 0.35, 0.4, 0.45)                      # revision 3
MEASURED = (0.08, 0.12)                            # revision 6: PIN1 imaging (median, uncorrected upper bound)


def params(rc, rin, sigma, **extra):
    return C.geo_params(rc, rin, RHO[(rc, rin)], RC, sigma_pin=sigma, **extra)


def s_data_frame(f):
    d = pd.read_csv(f)
    q = d["qDII"].values
    res, k = residual_sd(d[["aligned_x", "aligned_y", "aligned_z"]].values, np.log(np.maximum(q, 0.02)),
                         d["Auxin"].values, d["radial_distance"].values, extra_mask=q >= 0.02)
    return s_from(res, k), len(res), k


class Sampler(NoisySim):
    sample_from, sample_to = math.inf, -math.inf          # set per run; _geometry is already called inside __init__

    def _geometry(self, first=False):
        super()._geometry(first)
        if self.sample_from <= self.t <= self.sample_to and abs(self.t / 10.0 - round(self.t / 10.0)) < 1e-6 and len(self.A) == self.tis.n:
            pts = self.tis.pts * UM
            res, k = residual_sd(pts, np.log(np.maximum(self.A, 1e-9)), self.A, np.hypot(pts[:, 0], pts[:, 1]))
            self.res.append(res)
            self.ks.append(k)


def s_model_job(job):
    rin, sigma, seed = job
    sim = Sampler(params(RC, rin, sigma, t_end=400.0, mesh_seed=seed, seed=seed))
    sim.sample_from, sim.sample_to, sim.res, sim.ks = 200.0, 400.0, [], []
    sim.run()
    return s_from(np.concatenate(sim.res), float(np.mean(sim.ks)))


def s_model(pool, rin, sigma, seeds=(1, 2, 3, 4)):
    return float(np.mean(pool.map(s_model_job, [(rin, sigma, s) for s in seeds])))


def run_job(job):
    rin, sigma, seed, T = job
    if T is not None:
        sim = NoisySim(params(RC, rin, sigma, t_end=300.0, T=T, mesh_seed=seed, seed=seed)).run()
        return dict(rin=rin, sigma=sigma, seed=seed, T=T, n=len(sim.log))
    p = params(M.RC_START, rin, sigma, t_end=T1, mesh_seed=seed, seed=seed)
    sim = NoisySim(p, dict(T=M.T_RAMP, rc0=M.RC_START, rc1=RC, rho0=RHO[(M.RC_START, rin)], rho1=RHO[(RC, rin)], ds=M.SRC_OFFSET)).run()
    late = [l for l in sim.log if T0 <= l[0] < T1]
    s = analysis.summarize(late, sim.p["gamma"], skip=0.0) if len(late) >= 12 else dict(pattern="none")
    rs = noise_tools.rank_spread(late, kmax=5, skip=0.0) if len(late) >= 12 else [float("nan")] * 5
    return dict(rin=rin, sigma=sigma, seed=seed, T=None, pattern=s["pattern"], alpha=s.get("alpha"), f_alpha=s.get("f_alpha"),
                gap_cv=s.get("gap_cv"), G=s.get("G"), spread=float(np.nanmean(rs)),
                r_commit=float(np.median([math.hypot(l[1], l[2]) * UM for l in late])) if late else float("nan"))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    if which == "data":
        rows = []
        for f in sorted(DATA.rglob("*_aligned_L1_normalized_signal_data.csv")):
            s, n, k = s_data_frame(f)
            rows.append(dict(frame=f.parent.name, s=s, n=n, k=k))
            print(f"{f.parent.name:45s} s {s:.3f}  cells {n:3d}  mean neighbours {k:.1f}")
        v = np.array([r["s"] for r in rows if np.isfinite(r["s"])])
        print(f"s_data: median {np.median(v):.3f}  IQR {np.quantile(v, .25):.3f}-{np.quantile(v, .75):.3f}  frames {len(v)}")
        json.dump(dict(rows=rows, s_data=float(np.median(v))), open(OUT / "s_data.json", "w"), indent=1)
    elif which == "calib":
        target = json.load(open(OUT / "s_data.json"))["s_data"]
        out = {}
        with Pool(8) as pool:
            for rin in M.RHO_IN:
                s0 = s_model(pool, rin, 0.0)
                print(f"rho_in {rin:.0f}: s_model(0) = {s0:.3f}  (s_data {target:.3f})", flush=True)
                if s0 >= target:
                    out[rin] = dict(sigma=0.0, s=s0, steps=[(0.0, s0)])
                    continue
                lo, hi, steps = 0.01, 2.0, [(0.0, s0)]
                shi = s_model(pool, rin, hi)
                steps.append((hi, shi))
                if shi < target:
                    out[rin] = dict(sigma=None, s=shi, steps=steps)
                    print(f"  even sigma {hi} gives s {shi:.3f} < target", flush=True)
                    continue
                for _ in range(8):
                    mid = math.sqrt(lo * hi)
                    sm = s_model(pool, rin, mid)
                    steps.append((mid, sm))
                    print(f"  sigma {mid:.4f} -> s {sm:.3f}", flush=True)
                    lo, hi = (mid, hi) if sm < target else (lo, mid)
                sig = math.sqrt(lo * hi)
                out[rin] = dict(sigma=sig, s=s_model(pool, rin, sig), steps=steps)
                print(f"  sigma* = {sig:.4f}, s at sigma* = {out[rin]['s']:.3f}", flush=True)
        json.dump({str(k): v for k, v in out.items()}, open(OUT / "sigma.json", "w"), indent=1)
    elif which == "run":
        sig = {float(k): v["sigma"] for k, v in json.load(open(OUT / "sigma.json")).items()}
        jobs = [(rin, f * sig[rin], s, None) for rin in M.RHO_IN for f in (0.0, 0.5, 1.0) for s in range(1, 17)]
        jobs += [(rin, sig[rin], s, 0.0) for rin in M.RHO_IN for s in (1, 2, 3)]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "runs.json", "w"))
        print("done", len(res))
    elif which == "dose":
        jobs = [(rin, sg, s, None) for rin in M.RHO_IN for sg in DOSE for s in range(1, 17)]
        jobs += [(rin, 1.0, s, 0.0) for rin in M.RHO_IN for s in (1, 2, 3)]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "dose_runs.json", "w"))
        print("done", len(res))
    elif which == "dose_fine":
        jobs = [(rin, sg, s, None) for rin in M.RHO_IN for sg in FINE for s in range(1, 17)]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "dose_fine_runs.json", "w"))
        print("done", len(res))
    elif which == "dose_measured":
        jobs = [(rin, sg, s, None) for rin in M.RHO_IN for sg in MEASURED for s in range(1, 17)]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "dose_measured_runs.json", "w"))
        print("done", len(res))
    elif which == "dose_report":
        res = json.load(open(OUT / "dose_runs.json"))
        for extra in ("dose_fine_runs.json", "dose_measured_runs.json"):
            if (OUT / extra).exists():
                res += json.load(open(OUT / extra))
        grid = tuple(sorted({r["sigma"] for r in res if r["T"] is None}))
        print("data: non-canonical 15%, P1-P5 spread 6.7 deg, interval CV 0.22, angle 137.5, G 0.23, P0 radius 29.0 um")
        print("rho_in  sigma  patterns                                        regular  angle   non-can  spread  gap CV   G     r commit   T=0 primordia")
        for rin in M.RHO_IN:
            med = {}
            for sg in grid:
                rs = [r for r in res if r["rin"] == rin and r["sigma"] == sg and r["T"] is None]
                pats = {}
                for r in rs:
                    pats[r["pattern"]] = pats.get(r["pattern"], 0) + 1
                ps = ", ".join(f"{k} {v}" for k, v in sorted(pats.items(), key=lambda x: -x[1]))
                g = lambda k: float(np.nanmedian([r[k] if r[k] is not None else np.nan for r in rs]))
                reg = sum(not r["pattern"].endswith("~") and r["pattern"] != "none" for r in rs)
                ctl = [r["n"] for r in res if r["rin"] == rin and r["T"] == 0.0] if sg == 1.0 else []
                med[sg] = dict(nc=1 - g("f_alpha"), spread=g("spread"), cv=g("gap_cv"))
                print(f"{rin:4.0f}   {sg:5.2f}  {ps:46s}  {reg:3d}/16  {g('alpha'):6.1f}  {100 * med[sg]['nc']:5.0f}%  {med[sg]['spread']:5.1f}  "
                      f"{med[sg]['cv']:5.2f}  {g('G'):5.2f}  {g('r_commit'):6.1f}    {ctl}")
            mono = {k: all(med[a][k] <= med[b][k] for a, b in zip(grid, grid[1:])) for k in ("nc", "spread", "cv")}
            both = [sg for sg in grid if 0.09 <= med[sg]["nc"] <= 0.21 and 4.0 <= med[sg]["spread"] <= 9.4]

            def first_reach(key, target):
                if med[0.0][key] >= target:
                    return 0.0, "0"
                if med[0.25][key] >= target:
                    return 0.25, "<= 0.25"
                pos = [g for g in grid if g >= 0.25]
                for a, b in zip(pos, pos[1:]):
                    ya, yb = med[a][key], med[b][key]
                    if yb >= target:
                        f = (target - ya) / (yb - ya) if yb > ya else 1.0
                        v = math.exp(math.log(a) + f * (math.log(b) - math.log(a)))
                        return v, f"{v:.2f}"
                return math.inf, "> 1.0"
            nc, sp = first_reach("nc", 0.15), first_reach("spread", 6.7)
            need = max(nc, sp, key=lambda x: x[0])
            print(f"rho_in {rin:.0f}: N1 monotone {mono}; sigma reaching non-canonical 15%: {nc[1]}; spread 6.7 deg: {sp[1]}; sigma_need = {need[1]}; "
                  f"grid points with non-canonical 9-21% and spread 4.0-9.4 at once: {both or 'none'}")
    elif which == "report":
        res = json.load(open(OUT / "runs.json"))
        sig = {float(k): v["sigma"] for k, v in json.load(open(OUT / "sigma.json")).items()}
        print("data: non-canonical 15%, P1-P5 spread 6.7 deg, interval CV 0.22, angle 137.5, G 0.23, P0 radius 29.0 um")
        print("rho_in  sigma        patterns                              regular  angle   non-can  spread  gap CV   G     r commit   T=0 primordia")
        stats = {}
        for rin in M.RHO_IN:
            for f in (0.0, 0.5, 1.0):
                sg = f * sig[rin]
                rs = [r for r in res if r["rin"] == rin and abs(r["sigma"] - sg) < 1e-12 and r["T"] is None]
                pats = {}
                for r in rs:
                    pats[r["pattern"]] = pats.get(r["pattern"], 0) + 1
                ps = ", ".join(f"{k} {v}" for k, v in sorted(pats.items(), key=lambda x: -x[1]))
                g = lambda k: float(np.nanmedian([r[k] for r in rs if r[k] is not None]))
                reg = sum(not r["pattern"].endswith("~") and r["pattern"] != "none" for r in rs)
                ctl = [r["n"] for r in res if r["rin"] == rin and r["T"] == 0.0] if f == 1.0 else []
                stats[(rin, f)] = dict(nc=1 - g("f_alpha"), spread=g("spread"), cv=g("gap_cv"), reg=reg, ctl=ctl)
                print(f"{rin:4.0f}   {sg:6.3f} ({f:.1f}x)  {ps:36s}  {reg:3d}/16  {g('alpha'):6.1f}  {100 * (1 - g('f_alpha')):5.0f}%  {g('spread'):5.1f}  "
                      f"{g('gap_cv'):5.2f}  {g('G'):5.2f}  {g('r_commit'):6.1f}    {ctl}")
        print()
        for rin in M.RHO_IN:
            a, b, c = (stats[(rin, f)] for f in (0.0, 0.5, 1.0))
            mono = {k: a[k] <= b[k] <= c[k] for k in ("nc", "spread", "cv")}
            n2 = 0.09 <= c["nc"] <= 0.21 and 4.0 <= c["spread"] <= 9.4
            print(f"rho_in {rin:.0f}: N1 monotone {mono} -> {all(mono.values())};  N2 at sigma* (non-canonical 9-21% and spread 4.0-9.4): {n2};  "
                  f"N3 no primordia without transport: {all(x == 0 for x in c['ctl'])}")
