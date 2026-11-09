"""Model side of the scale calibration (PROTOCOL.md). The frozen main line v2 is used unchanged; only the
geometry (ring radius) and, by the old rule, the peripheral production change.

python run.py calib      # derived geometry from out/measure_nuclei_21.json, then rho_far at the new geometry
python run.py run        # 16 seeds per rho_in: calibrated geometry, and the uncalibrated main line for comparison
python run.py report
"""
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "frozen_v2"))
sys.path.insert(1, str(HERE))

import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

import analysis  # noqa: E402
import mainline as M  # noqa: E402
import noise_tools  # noqa: E402
from layer import TwoLayerSim  # noqa: E402
from measure import az_width  # noqa: E402

OUT = HERE / "out"
TARGET, T0, T1, T_WIDTH = 4.0, 1250.0, 1700.0, 1550.0
SEEDS = range(1, 17)


def geo_params(rc, rin, rho, rc_end, **extra):
    """mainline.params with the final ring radius and peripheral production given explicitly."""
    p = dict(M.OP, w=M.W, R_c=rc, R_p=rc + 2.0, R_out=rc_end + 9.0, rho_cz=rin, rho_pz=rin, rho_prox=rin,
             R_src=rc + 2.0 + M.SRC_OFFSET, rho_far=rho, kappa_c=M.KAPPA_C, pin_cz=0.2, Th=M.TH,
             **M.TRACK, **M.READOUT, **M.LAYER)
    p.update(extra)
    return p


assert geo_params(5.5, 2.0, M.RHO_FAR[(5.5, 2.0)], 5.5) == M.params(5.5, 2.0), "geo_params must reproduce the main line"


def ring_level(sim, t=40.0):
    sim.A2 = np.zeros(sim.tis.n)
    A = sim.A.copy()
    for _ in range(int(t / sim.p["dt"])):
        A = sim._step(A)
    ring = (sim.rad >= sim.p["R_c"]) & (sim.rad < sim.p["R_p"])
    return float(A[ring].mean())


def calib_job(job):
    rc, rin, rc_end = job
    sim = TwoLayerSim(geo_params(rc, rin, 10.0, rc_end, Th=1e9, t_end=1.0, init_frac=1.0))
    lo, hi = 0.2, 4000.0
    for _ in range(15):
        mid = (lo * hi) ** 0.5
        sim.p["rho_far"] = mid
        sim.G["rho"] = sim._rho(sim.rad)
        if ring_level(sim) < TARGET:
            lo = mid
        else:
            hi = mid
    rho = (lo * hi) ** 0.5
    sim.p["rho_far"] = rho
    sim.G["rho"] = sim._rho(sim.rad)
    on = ring_level(sim, 60.0)
    sim.p["T"] = 0.0
    off = ring_level(sim, 60.0)
    return dict(rc=rc, rin=rin, rc_end=rc_end, rho_far=rho, ring=on, ratio_T0=off / on)


def model_spacing(rc_end):
    sim = TwoLayerSim(geo_params(rc_end, 0.0, 1.0, rc_end, t_end=60.0, Th=1e9)).run()
    P = sim.tis.pts
    r = np.hypot(P[:, 0], P[:, 1])
    nn = cKDTree(P).query(P, k=2)[0][:, 1]
    return float(np.median(nn[r < sim.p["R_out"] - 2]))


class Recorder(TwoLayerSim):
    """Records, for primordia fixed in [T0, T_WIDTH], the P0 azimuthal width with the data's code (in um)."""
    um = 1.0

    def _add_primordium(self, x, y, t0=None):
        q = super()._add_primordium(x, y, t0)
        if T0 <= self.t <= T_WIDTH and self.A is not None and len(self.A) == self.tis.n:
            u, pts = self.um, self.tis.pts
            w, note = az_width(pts[:, 0] * u, pts[:, 1] * u, self.A, (x * u, y * u), math.hypot(x, y) * u)
            self.widths.append(w)
        return q


def run_job(job):
    name, rin, rc_end, rho_s, rho_e, seed, um = job
    p = geo_params(M.RC_START, rin, rho_s, rc_end, t_end=T1, mesh_seed=seed, seed=seed)
    sim = Recorder(p, dict(T=M.T_RAMP, rc0=M.RC_START, rc1=rc_end, rho0=rho_s, rho1=rho_e, ds=M.SRC_OFFSET))
    sim.um, sim.widths = um, []
    sim.run()
    late = [l for l in sim.log if T0 <= l[0] < T1]
    s = analysis.summarize(late, sim.p["gamma"], skip=0.0) if len(late) >= 12 else dict(pattern="none")
    radii = [math.hypot(l[1], l[2]) * um for l in late]
    rs = noise_tools.rank_spread(late, kmax=5, skip=0.0) if len(late) >= 12 else [float("nan")] * 5
    return dict(name=name, rin=rin, seed=seed, pattern=s["pattern"], alpha=s.get("alpha"), f_alpha=s.get("f_alpha"),
                gap=s.get("gap_mean"), gap_cv=s.get("gap_cv"), G=s.get("G"), spread=float(np.nanmean(rs)),
                r_commit=float(np.median(radii)) if radii else float("nan"),
                widths=[w for w in sim.widths if w is not None], n_width_failed=sum(w is None for w in sim.widths))


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    if which == "calib":
        meas = json.load(open(OUT / "measure_nuclei_21.json"))
        d = np.array([m["d"] for m in meas if m["d"]])
        cz = np.array([m["clv3_radius"] for m in meas if m["clv3_radius"]])
        d_model = model_spacing(M.RC_END)
        um = float(np.median(d)) / d_model
        rc_end = float(np.median(cz)) / um
        print(f"meristems {len(meas)}; d median {np.median(d):.2f} um (IQR {np.quantile(d, .25):.2f}-{np.quantile(d, .75):.2f}); "
              f"CZ radius median {np.median(cz):.1f} um (IQR {np.quantile(cz, .25):.1f}-{np.quantile(cz, .75):.1f})")
        print(f"model cell spacing {d_model:.3f} units -> {um:.3f} um per unit; ring inner radius {rc_end:.2f} units (main line 5.50)")
        jobs = [(rc, rin, rc_end) for rc in (M.RC_START, rc_end) for rin in M.RHO_IN]
        with Pool(4) as pool:
            res = pool.map(calib_job, jobs)
        for r in res:
            print(f"ring {r['rc']:.2f}  rho_in {r['rin']:.0f}  rho_far {r['rho_far']:.3f}  free ring {r['ring']:.2f}  "
                  f"ring(T=0)/ring {r['ratio_T0']:.2f} {'ok' if r['ratio_T0'] < 0.82 else 'FAILS R0'}")
        json.dump(dict(um=um, d_model=d_model, rc_end=rc_end, calib=res), open(OUT / "geometry.json", "w"), indent=1)
    elif which == "run":
        g = json.load(open(OUT / "geometry.json"))
        rho = {(r["rc"], r["rin"]): r["rho_far"] for r in g["calib"]}
        jobs = [("calibrated", rin, g["rc_end"], rho[(M.RC_START, rin)], rho[(g["rc_end"], rin)], s, g["um"]) for rin in M.RHO_IN for s in SEEDS]
        jobs += [("main line", rin, M.RC_END, M.RHO_FAR[(M.RC_START, rin)], M.RHO_FAR[(M.RC_END, rin)], s, g["um"]) for rin in M.RHO_IN for s in SEEDS]
        with Pool(28) as pool:
            res = pool.map(run_job, jobs)
        json.dump(res, open(OUT / "runs.json", "w"))
        print("done", len(res))
    elif which == "report":
        res = json.load(open(OUT / "runs.json"))
        meas = json.load(open(OUT / "measure_nuclei_21.json"))
        pr = np.array([m["p0_radius_t00"] for m in meas if m["p0_radius_t00"]])
        pw = np.array([m["p0_width_t00"] for m in meas if m["p0_width_t00"]])
        print(f"data: P0 radius at 0 h median {np.median(pr):.1f} um (IQR {np.quantile(pr, .25):.1f}-{np.quantile(pr, .75):.1f}, n={len(pr)}); "
              f"P0 azimuthal width median {np.median(pw):.1f} um (IQR {np.quantile(pw, .25):.1f}-{np.quantile(pw, .75):.1f}, n={len(pw)})")
        print("paper: angle 137.5, P1-P5 spread 6.7 deg, interval CV 0.22, non-canonical 15% (Besnard WT)")
        print("model            rho_in  patterns                         angle   non-can  spread  gap CV   G     r at commit (um)  P0 width (um)")
        for name in ("main line", "calibrated"):
            for rin in M.RHO_IN:
                rs = [r for r in res if r["name"] == name and r["rin"] == rin]
                pats = {}
                for r in rs:
                    pats[r["pattern"]] = pats.get(r["pattern"], 0) + 1
                ps = ", ".join(f"{k} {v}" for k, v in sorted(pats.items(), key=lambda x: -x[1]))
                g = lambda k: np.nanmedian([r[k] for r in rs if r[k] is not None])
                w = sum((r["widths"] for r in rs), [])
                print(f"{name:15s}  {rin:4.0f}    {ps:32s} {g('alpha'):6.1f}  {100 * (1 - g('f_alpha')):5.0f}%  {g('spread'):5.1f}  {g('gap_cv'):5.2f}  "
                      f"{g('G'):5.2f}   {g('r_commit'):6.1f}          {np.median(w) if w else float('nan'):6.1f} (n={len(w)})")
