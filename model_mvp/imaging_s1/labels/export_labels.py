"""Material for Codex to correct the P labels (PROTOCOL revision 4). Development group only; auxin input only (no DR5).

Writes labels/package/ and labels/label_package.zip (handed over), labels/out/label_key.json (kept here).
"""
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects  # noqa: F401
import numpy as np
import pandas as pd
from matplotlib.collections import PolyCollection
from scipy.spatial import Voronoi

HERE = Path(__file__).resolve().parent
G = json.load(open(HERE.parent / "groups.json"))
DATA = HERE.parents[2] / "reproductions" / "elife55832" / "outputs" / "nuclei_21"
PKG = HERE / "package"
FR = ("t00", "t05", "t10")
RMAX = 72.0


def frame_files(seq, fr):
    l1 = next((DATA / seq).rglob(f"*_{fr}_aligned_L1_normalized_signal_data.csv"))
    return l1, Path(str(l1).replace("aligned_L1_normalized_signal_data", "all_extrema")), \
        Path(str(l1).replace("aligned_L1_normalized_signal_data", "aligned_primordia_extrema"))


def cellmap(ax, x, y, v, vmin, vmax):
    xy = np.c_[x, y]
    ghost = (RMAX + 30) * np.c_[np.cos(np.linspace(0, 2 * np.pi, 90)), np.sin(np.linspace(0, 2 * np.pi, 90))]
    vor = Voronoi(np.vstack([xy, ghost]))
    polys, vals = [], []
    for k in range(len(xy)):
        reg = vor.regions[vor.point_region[k]]
        if reg and -1 not in reg:
            polys.append(vor.vertices[reg]); vals.append(v[k])
    pc = PolyCollection(polys, array=np.array(vals), cmap="viridis", edgecolors=(0, 0, 0, 0.15), linewidths=0.15)
    pc.set_clim(vmin, vmax); ax.add_collection(pc)
    pc.set_clip_path(plt.Circle((0, 0), RMAX, transform=ax.transData))
    return pc


def main():
    if PKG.exists():
        shutil.rmtree(PKG)
    (PKG / "data").mkdir(parents=True); (PKG / "images").mkdir()
    rng = np.random.default_rng(1128)
    names = list(G["development"])
    order = rng.permutation(len(names))
    key = {}
    for k, i in enumerate(order, start=1):
        code = f"S{k:02d}"
        key[code] = names[i]
        seq = names[i]
        th = np.linspace(0, 2 * np.pi, 200)
        for j, fr in enumerate(FR):
            l1f, exf, prf = frame_files(seq, fr)
            d = pd.read_csv(l1f, usecols=["aligned_x", "aligned_y", "qDII", "clv3_radius"])
            ex = pd.read_csv(exf); ex = ex[ex.extremum_type == "minimum"].copy()
            pr = pd.read_csv(prf); pr = pr[pr.extremum_type == "minimum"]
            auto = dict(zip(pr.label, pr.primordium))
            ex["auto_P"] = ex.label.map(auto)
            rc = float(d.clv3_radius.iloc[0])
            out_n = pd.DataFrame(dict(x_um=d.aligned_x, y_um=d.aligned_y, auxin_input=1 - d.qDII, qDII=d.qDII))
            out_n.to_csv(PKG / "data" / f"{code}_{fr[1:]}h_nuclei.csv", index=False, float_format="%.4f")
            out_e = pd.DataFrame(dict(max_id=ex.label.astype(int), x_um=ex.aligned_x, y_um=ex.aligned_y, r_um=ex.radial_distance,
                                      theta_deg=ex.aligned_theta, auxin_input_normalized=1 - ex.Normalized_qDII,
                                      extremality=ex.extremality, area=ex.area, auto_P=ex.auto_P))
            out_e.to_csv(PKG / "data" / f"{code}_{fr[1:]}h_maxima.csv", index=False, float_format="%.3f")
            fig, ax = plt.subplots(figsize=(10, 9.2))
            pc = cellmap(ax, d.aligned_x.values, d.aligned_y.values, (1 - d.qDII).values, 0.55, 1.0)
            ax.plot(rc * np.cos(th), rc * np.sin(th), "--", color="w", lw=1.2)
            for _, q in ex.iterrows():
                ax.plot(q.aligned_x, q.aligned_y, "o", ms=11, mfc="none", mec="r", mew=1.5, clip_on=False)
                ax.text(q.aligned_x + 1.6, q.aligned_y + 1.4, f"{int(q.label)}", color="r", fontsize=11, fontweight="bold",
                        path_effects=[matplotlib.patheffects.withStroke(linewidth=2, foreground="w")])
                if pd.notna(q.auto_P):
                    ax.text(q.aligned_x + 1.6, q.aligned_y - 4.6, f"auto P{int(q.auto_P)}", color="k", fontsize=8.5,
                            path_effects=[matplotlib.patheffects.withStroke(linewidth=2, foreground="w")])
            ax.set_xlim(-RMAX, RMAX); ax.set_ylim(-RMAX, RMAX); ax.set_aspect("equal")
            ax.set_xticks(range(-70, 71, 10)); ax.set_yticks(range(-70, 71, 10)); ax.tick_params(labelsize=8)
            ax.grid(color="w", lw=0.3, alpha=0.5)
            ax.set_title(f"{code}   {int(fr[1:])} h", fontsize=14)
            fig.colorbar(pc, ax=ax, shrink=0.75, label="auxin input (1 - qDII)")
            fig.text(0.5, 0.015, "red circle + number: detected auxin-input maximum (max_id); black 'auto P': authors' automatic label; "
                     "white dashed circle: CLV3 radius", ha="center", fontsize=9)
            fig.savefig(PKG / "images" / f"{code}_{fr[1:]}h.png", dpi=105)
            plt.close(fig)
        print(code, "done", flush=True)
    (HERE / "out").mkdir(exist_ok=True)
    json.dump(dict(note="Code -> meristem. Keep in the project; never hand over.", seed=1128, key=key), open(HERE / "out" / "label_key.json", "w"), indent=1)
    shutil.copy(HERE / "CODEX_LABEL_INSTRUCTIONS.md", PKG / "README.md")
    shutil.make_archive(str(HERE / "label_package"), "zip", PKG)


if __name__ == "__main__":
    main()
