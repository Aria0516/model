import sys
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from curvlib import load_seq, apex, smooth
S = sys.argv[1]
seq = load_seq(S)
c = apex(seq["t00"])
fig, ax = plt.subplots(2, 3, figsize=(12, 8))
for j, fr in enumerate(("t00", "t05", "t10")):
    d = seq[fr].copy(); d["x"] -= c[0]; d["y"] -= c[1]
    for i, (rad, lab) in enumerate(((0.0, "raw H"), (5.0, "H median 5um"))):
        v = d.H.values if rad == 0 else smooth(d, "H", rad)
        sc = ax[i, j].scatter(d.x, d.y, c=v, cmap="RdBu_r", vmin=-0.06, vmax=0.06, s=14)
        ax[i, j].tricontour(d.x, d.y, d.z, levels=12, colors="k", linewidths=0.4)
        ax[i, j].set_aspect("equal"); ax[i, j].set_title(f"{fr} {lab}")
        for r in (20, 55): ax[i, j].add_patch(plt.Circle((0, 0), r, fill=False, ls=":"))
plt.colorbar(sc, ax=ax); fig.savefig(sys.argv[2], dpi=80)
print("apex", c)
