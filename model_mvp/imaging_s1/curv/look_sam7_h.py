import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from curvlib import load_seq, apex
seq = load_seq(sys.argv[1]); c = apex(seq["t00"])
fig, ax = plt.subplots(1, 3, figsize=(13, 4.5))
for j, fr in enumerate(("t00", "t05", "t10")):
    d = seq[fr]; x, y, z = d.x - c[0], d.y - c[1], d.z
    r2 = x**2 + y**2
    m = np.sqrt(r2) < 45
    X = np.c_[np.ones(m.sum()), x[m], y[m], r2[m], r2[m]**2]
    beta = np.linalg.lstsq(X, z[m], rcond=None)[0]
    res = z - np.c_[np.ones(len(x)), x, y, r2, r2**2] @ beta
    sc = ax[j].scatter(x, y, c=res, cmap="RdBu_r", vmin=-4, vmax=4, s=14)
    ax[j].set_aspect("equal"); ax[j].set_title(f"{fr} height residual (um)")
    for r in (20, 45, 55): ax[j].add_patch(plt.Circle((0, 0), r, fill=False, ls=":"))
    print(fr, "residual sd within 45um %.2f" % res[m].std())
plt.colorbar(sc, ax=ax); fig.savefig(sys.argv[2], dpi=80)
