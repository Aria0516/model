"""Blind material for the second labeller (Codex). Development group only; morphology only; random codes.

Writes package/ (to be zipped and handed over) and out/blind_key.json (kept in the project, NOT handed over).
"""
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np

from curvlib import FRAMES, apex, load_seq

HERE = Path(__file__).resolve().parent
G = json.load(open(HERE.parent / "groups.json"))
DATA = HERE.parents[2] / "reproductions" / "elife55832" / "outputs" / "nuclei_21"
PKG = HERE / "package"
LIM = 62.0


def hillshade(ax, x, y, z):
    tri = mtri.Triangulation(x, y)
    p = np.c_[x, y, z][tri.triangles]
    e = np.max(np.linalg.norm(p[:, [0, 1, 2]] - p[:, [1, 2, 0]], axis=2), axis=1)
    tri.set_mask(e > 12.0)                                   # drop long hull triangles
    nrm = np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0])
    nrm /= np.linalg.norm(nrm, axis=1)[:, None]
    nrm *= np.sign(nrm[:, 2])[:, None]
    light = np.array([-1.0, 1.0, 0.65]); light /= np.linalg.norm(light)     # low light (about 25 deg) to bring out small relief
    shade = nrm @ light
    ax.tripcolor(tri, facecolors=shade, cmap="gray", vmin=np.percentile(shade, 2), vmax=np.percentile(shade, 98))
    ax.tricontour(tri, z, levels=np.arange(np.floor(z.min()), z.max(), 2.0), colors="#d95f02", linewidths=0.35)


def dome_residual(x, y, z):
    """Generic view: height minus a best-fit quadratic surface (z = a + b x + c y + d r^2) over r < 50 um.
    Simpler than the automatic criterion's fit (which adds an r^4 term and uses r < 45 um)."""
    r2 = x ** 2 + y ** 2
    m = r2 < 50.0 ** 2
    A = np.c_[np.ones(len(x)), x, y, r2]
    return z - A @ np.linalg.lstsq(A[m], z[m], rcond=None)[0]


def page(code, seq, c, path):
    fig, axes = plt.subplots(3, 3, figsize=(15, 15.6))
    for j, fr in enumerate(FRAMES):
        d = seq[fr]
        x, y, z = d.x.values - c[0], d.y.values - c[1], d.z.values
        hillshade(axes[0, j], x, y, z)
        res = dome_residual(x, y, z)
        sr = axes[1, j].scatter(x, y, c=res, cmap="PuOr_r", vmin=-4, vmax=4, s=16)
        sc = axes[2, j].scatter(x, y, c=d.H.values, cmap="RdBu_r", vmin=-0.05, vmax=0.05, s=16)
        for i in range(3):
            ax = axes[i, j]
            ax.set_xlim(-LIM, LIM); ax.set_ylim(-LIM, LIM); ax.set_aspect("equal")
            ax.set_xticks(range(-60, 61, 10)); ax.set_yticks(range(-60, 61, 10)); ax.tick_params(labelsize=7)
            ax.grid(color="#3182bd", lw=0.3, alpha=0.6)
        axes[0, j].set_title(f"{code}  {fr[1:]} h  surface relief, low light (orange: 2 um contours)", fontsize=9)
        axes[1, j].set_title(f"{code}  {fr[1:]} h  height minus fitted dome (um)", fontsize=9)
        axes[2, j].set_title(f"{code}  {fr[1:]} h  mean curvature (1/um)", fontsize=9)
    fig.colorbar(sr, ax=axes[1, :], shrink=0.7)
    fig.colorbar(sc, ax=axes[2, :], shrink=0.7)
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main():
    if PKG.exists():
        shutil.rmtree(PKG)
    (PKG / "data").mkdir(parents=True); (PKG / "images").mkdir()
    rng = np.random.default_rng(20261128)
    names = list(G["development"])
    order = rng.permutation(len(names))
    key = {}
    for k, i in enumerate(order, start=1):
        code = f"M{k:02d}"
        key[code] = names[i]
        seq = load_seq(DATA / names[i])
        c = apex(seq["t00"])
        for fr in FRAMES:
            d = seq[fr]
            out = np.c_[d.x - c[0], d.y - c[1], d.z, d.H, d.K]
            np.savetxt(PKG / "data" / f"{code}_{fr[1:]}h.csv", out, delimiter=",", fmt="%.4f",
                       header="x_um,y_um,z_um,mean_curvature,gaussian_curvature", comments="")
        page(code, seq, c, PKG / "images" / f"{code}.png")
        print(code, "done", flush=True)
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(dict(note="Code -> meristem. Keep in the project; never hand over with the package.", seed=20261128, key=key),
              open(HERE / "out" / "blind_key.json", "w"), indent=1)
    shutil.copy(HERE / "CODEX_INSTRUCTIONS.md", PKG / "README.md")
    shutil.make_archive(str(HERE / "codex_package"), "zip", PKG)


if __name__ == "__main__":
    main()
