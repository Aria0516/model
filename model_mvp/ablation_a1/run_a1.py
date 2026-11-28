"""Paired ablation A1 (PROTOCOL.md): field on vs field off (k_rel = 0), 120 v3 samples x seeds 1, 2.

python run_a1.py [n_proc]     # writes out/events_<cond>_<i>_<seed>.json, skipping files that exist
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent / "detuned_v3"
sys.path.insert(0, str(V3 / "frozen_v3"))
import mainline_v3 as V  # noqa: E402

OUT = HERE / "out"
GEO = json.load(open(HERE.parent / "calib_v2" / "out" / "geometry.json"))
SAMPLES = json.load(open(V3 / "out" / "samples.json"))
CAL = {int(k): v for k, v in json.load(open(V3 / "out" / "calib.json")).items()}


def job(arg):
    cond, i, seed = arg
    f = OUT / f"events_{cond}_{i:03d}_{seed}.json"
    if f.exists():
        return str(f.name)
    s = dict(SAMPLES[i])
    if cond == "off":
        s["k_rel"] = 0.0
    sim = V.make(s, s["rho_in"], GEO["rc_end"], CAL[i]["start"], CAL[i]["end"], seed).run()
    json.dump(dict(cond=cond, i=i, seed=seed, k_rel=s["k_rel"], gamma=sim.p["gamma"], log=[list(map(float, l)) for l in sim.log]),
              open(f.with_suffix(".tmp"), "w"))
    f.with_suffix(".tmp").rename(f)
    return str(f.name)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    jobs = [(c, i, s) for i in range(len(SAMPLES)) for s in (1, 2) for c in ("on", "off")]
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    with Pool(n) as pool:
        for k, name in enumerate(pool.imap_unordered(job, jobs), start=1):
            if k % 20 == 0:
                print(f"{k}/{len(jobs)} {name}", flush=True)
    print("done", len(jobs))
