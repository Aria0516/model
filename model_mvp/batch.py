"""Parallel batch runner: python batch.py jobs.json [out.jsonl]

jobs.json is a list of [name, {param overrides}]. Prints one summary line per job.
"""
import json
import sys
import traceback
from multiprocessing import Pool

import analysis
from model import Sim


def one(job):
    name, over = job
    try:
        sim = Sim(over).run()
        s = analysis.summarize(sim.log, sim.p["gamma"])
        s.update(name=name, over=over, wall=sim.wall, cells=sim.tis.n,
                 ghost=sim.ghost_sum / max(sim.geo_count, 1), ring_A=sim.ring_mean_sum / max(sim.geo_count, 1))
        if sim.dg_n:
            s.update(prof=(sim.dg_prof / sim.dg_n).round(3).tolist(), pin_in=(sim.dg_in / sim.dg_n).round(3).tolist(),
                     pin_in_free=(sim.dg_in_free / sim.dg_n).round(3).tolist())
        if sim.track:
            import numpy as np
            lags, amax = [], []
            for pid, tr in sim.track.items():
                tr = np.array(tr)
                if len(tr) < 40 or tr[0, 0] < sim.p["t_end"] / 3:
                    continue
                age = tr[:, 0] - tr[0, 0]
                a_peak = age[np.argmax(tr[:, 2])]
                above = np.where(tr[:, 4] >= 0.5)[0]
                if len(above):
                    lags.append(age[above[0]] - a_peak); amax.append(a_peak)
            if lags:
                s.update(dr5_lag=float(np.median(lags)), auxin_peak_age=float(np.median(amax)), n_lag=len(lags))
        return s
    except Exception as e:                              # report, do not hide
        return dict(name=name, over=over, pattern="ERROR", error=f"{type(e).__name__}: {e}",
                    tb=traceback.format_exc()[-400:])


if __name__ == "__main__":
    jobs = json.load(open(sys.argv[1]))
    outp = sys.argv[2] if len(sys.argv) > 2 else None
    res = []
    with Pool(min(len(jobs), 28)) as pool:
        for s in pool.imap(one, jobs):
            res.append(s)
            if s["pattern"] == "ERROR":
                print(f"{s['name']:34s} ERROR {s['error']}", flush=True)
            else:
                print(f"{s['name']:34s} {analysis.fmt(s)}", flush=True)
    if outp:
        with open(outp, "w") as f:
            for s in res:
                f.write(json.dumps(s) + "\n")
