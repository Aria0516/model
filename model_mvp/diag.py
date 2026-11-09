"""python diag.py out.png key=value ...  -> one run with diagnostic figure and summary line."""
import sys
import analysis
import viz
from model import DEFAULT, Sim

if __name__ == "__main__":
    over = dict(snap_dt=10.0, kymo=1, v_div=1.25)
    for kv in sys.argv[2:]:
        k, v = kv.split("=")
        over[k] = v if isinstance(DEFAULT.get(k, 0.0), str) else float(v)
        if isinstance(DEFAULT.get(k), int) and not isinstance(DEFAULT.get(k), bool):
            over[k] = int(float(v))
    sim = Sim(over).run(verbose=True)
    s = analysis.summarize(sim.log, sim.p["gamma"])
    print(analysis.fmt(s))
    viz.diagnostic(sim, sys.argv[1], title=" ".join(sys.argv[2:]) + "   |   " + s["pattern"])
    print("saved", sys.argv[1])
