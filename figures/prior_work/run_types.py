"""Run the three pattern-type examples (same settings as model_mvp/figs.py fig_types) and save snapshots.

    python run_types.py      -> types.npz (cells, auxin, PIN vectors, primordia, initiation log)
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "model_mvp"))

from e10_phase_sub import OP  # noqa: E402
from model import Sim  # noqa: E402

CASES = [("distichous", 2.5), ("spiral", 3.5), ("decussate", 6.0)]

if __name__ == "__main__":
    out = {}
    for name, rc in CASES:
        sim = Sim(dict(OP, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0, t_end=800.0, mesh_seed=1, seed=1, snap_dt=799.0)).run()
        sn = sim.snaps[-1]
        out[f"{name}_pts"] = sn["pts"]; out[f"{name}_A"] = sn["A"]; out[f"{name}_pin"] = sn["pin"]
        out[f"{name}_prim"] = np.array([(x, y, i, a) for (x, y, i, a) in sn["prim"]])
        out[f"{name}_log"] = np.array(sim.log)
        out[f"{name}_par"] = np.array(json.dumps({k: sim.p[k] for k in ("R_c", "R_p", "R_out", "w", "gamma")}))
        print(name, "cells", len(sn["pts"]), "primordia", len(sim.log), "wall %.0fs" % sim.wall, flush=True)
    np.savez(HERE / "types.npz", **out)
