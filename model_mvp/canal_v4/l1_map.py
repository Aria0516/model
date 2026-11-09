"""Where does the epidermis form convergence points by itself? Sink-free tissue (no primordia, no drains),
final geometry, main line v2 otherwise; azimuthal variation of ring auxin after relaxation, against the
polarisation gain b and the centripetal bias kappa_c. A mechanics map, no pattern statistics.

python l1_map.py
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "frozen_v2"))
sys.path.insert(1, str(HERE.parent / "calib_v2"))

import numpy as np  # noqa: E402

import run as C  # noqa: E402
from layer import TwoLayerSim  # noqa: E402

GEO = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))
RC = GEO["rc_end"]
RHO = {(r["rc"], r["rin"]): r["rho_far"] for r in GEO["calib"]}


def job(j):
    rin, b, kc = j
    p = C.geo_params(RC, rin, RHO[(RC, rin)], RC, Th=1e9, t_end=1.0, b=b, kappa_c=kc, mesh_seed=1, seed=1)
    sim = TwoLayerSim(p)
    A = sim.A.copy()
    for _ in range(int(150.0 / sim.p["dt"])):
        A = sim._step(A)
    rad, pts = sim.rad, sim.tis.pts
    ring = (rad >= sim.p["R_c"]) & (rad < sim.p["R_p"])
    coef = np.polyfit(rad[ring], A[ring], 1)                       # remove the radial trend
    cv_az = float((A[ring] - np.polyval(coef, rad[ring])).std() / A[ring].mean())
    nbmax = np.full(len(A), -np.inf)
    np.maximum.at(nbmax, sim.tis.src, A[sim.tis.dst])
    peaks = ring & (A > nbmax) & (A > 1.1 * A[ring].mean())
    return dict(rin=rin, b=b, kc=kc, ring=float(A[ring].mean()), cv_az=cv_az, peaks=int(peaks.sum()), amax=float(A[ring].max()))


if __name__ == "__main__":
    jobs = [(rin, b, kc) for rin in (0.0, 2.0) for b in (2.0, 3.0, 4.0, 6.0) for kc in (0.0, 0.5, 1.0, 1.5)]
    with Pool(28) as pool:
        res = pool.map(job, jobs)
    print("azimuthal CV of ring auxin (radial trend removed) / ring peaks >1.1x mean / ring mean; sink-free, final geometry")
    for rin in (0.0, 2.0):
        print(f"\nrho_in {rin:.0f}        " + "".join(f"kappa_c {kc:<12}" for kc in (0.0, 0.5, 1.0, 1.5)))
        for b in (2.0, 3.0, 4.0, 6.0):
            cells = [r for r in res if r["rin"] == rin and r["b"] == b]
            cells.sort(key=lambda r: r["kc"])
            print(f"  b {b:3.1f}   " + "".join(f"{r['cv_az']:.3f}/{r['peaks']:2d}/{r['ring']:4.1f}     " for r in cells))
