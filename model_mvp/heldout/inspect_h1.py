"""Look at the raw angle sequences of H1 (no simulation; reads out/H1.json)."""
import json
from pathlib import Path

import numpy as np

res = json.load(open(Path(__file__).resolve().parent / "out" / "H1.json"))
ctrl = {r["seed"]: r for r in res if not r["treat"]}
trt = {r["seed"]: r for r in res if r["treat"]}
print("seed  control: next 6 signed angles          | treated: next 6 signed angles          | end pattern")
for s in range(1, 9):
    c = " ".join(f"{a:5.0f}" for a in ctrl[s]["angles_after"][:6])
    t = " ".join(f"{a:5.0f}" for a in trt[s]["angles_after"][:6])
    print(f"{s:3d}   {c}   | {t}   | {trt[s]['pattern']}")
fold = lambda x: np.minimum(x, 360 - np.asarray(x))
first = fold([trt[s]["angles_after"][0] for s in trt]); cf = fold([ctrl[s]["angles_after"][0] for s in ctrl])
print(f"angle from the treated primordium to the next one (folded): treated median {np.median(first):.0f} "
      f"(range {first.min():.0f}-{first.max():.0f}); control median {np.median(cf):.0f} (range {cf.min():.0f}-{cf.max():.0f})")
