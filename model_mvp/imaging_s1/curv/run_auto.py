"""Run the frozen automatic bulge criterion (PROTOCOL revision 2) on the development group only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from bulge import classify
from curvlib import load_seq

HERE = Path(__file__).resolve().parent
G = json.load(open(HERE.parent / "groups.json"))
DATA = HERE.parents[2] / "reproductions" / "elife55832" / "outputs" / "nuclei_21"
OUT = HERE / "out"; OUT.mkdir(exist_ok=True)

rows = []
for name in G["development"]:
    sites, c, det = classify(load_seq(DATA / name))
    for k, s in enumerate(sites):
        rows.append(dict(meristem=name, site=k, first_visible=s["first_visible"], frames="+".join(s["frames"]), x=round(s["x"], 2),
                         y=round(s["y"], 2), r=round(s["r"], 2), n_nuclei=s["n"], label=s["label"],
                         interval="" if s["interval"] is None else f"({s['interval'][0]},{s['interval'][1]}]"))
    print(f"{name[-22:]:22s} bulges per frame " + " ".join(f"{fr}:{len(det[fr][0])}" for fr in det)
          + f" | sites {len(sites)} events {sum(s['label'] == 'event' for s in sites)}")
df = pd.DataFrame(rows)
df.to_csv(OUT / "auto_sites_development.csv", index=False)
ev = df[df.label == "event"].groupby("meristem").size().reindex(G["development"], fill_value=0)
print("\nlabels:", df.label.value_counts().to_dict())
print(f"automatic side only: meristems with >=1 event {int((ev > 0).sum())}/14 (standard >= 8); events {int(ev.sum())} (standard >= 20); "
      f"largest share {ev.max() / max(ev.sum(), 1):.2f} (standard <= 0.25)")
print("intervals:", df[df.label == "event"].interval.value_counts().to_dict())
