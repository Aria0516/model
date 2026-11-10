"""One run of the frozen main line (model_mvp/frozen_v2) for the 3D schematic in Fig. 2A.

    python run_mech.py      -> mech.npz (epidermis and inner-layer auxin, PIN vectors, primordia, zones)
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "model_mvp" / "frozen_v2"))

from mainline import make  # noqa: E402
from model import pin_vectors  # noqa: E402

if __name__ == "__main__":
    sim = make(rin=2.0, seed=1, t_end=1700.0).run()
    p = sim.p
    prim = np.array([(q["x"], q["y"], q["id"], sim.t - q["tc"]) for q in sim.prim])
    np.savez(HERE / "mech.npz", pts=sim.tis.pts, A=sim.A, A2=sim.A2, R=sim.R, pin=pin_vectors(sim.A, sim.G, p),
             prim=prim, log=np.array(sim.log),
             par=np.array(json.dumps({k: p[k] for k in ("R_c", "R_p", "R_src", "R_out", "w", "gamma")})))
    print("cells", sim.tis.n, "primordia", len(sim.log), "wall %.0fs" % sim.wall)
