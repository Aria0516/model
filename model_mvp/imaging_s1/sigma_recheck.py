"""PROTOCOL revision 1: cell-to-cell PIN1 variation with the noise_v3 procedure, unchanged, on wall tables whose
side columns are renamed to their geometric side (left_X <-> right_X). noise_v3 files are not modified.

python sigma_recheck.py
"""
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "noise_v3"))
import pin1_measure as N  # noqa: E402

rows = []
with tempfile.TemporaryDirectory() as tmp:
    for f in sorted(N.DATA.rglob("*_walls.csv")):
        w = pd.read_csv(f)
        sw = w.rename(columns={"left_PIN1": "right_PIN1", "right_PIN1": "left_PIN1", "left_PI": "right_PI", "right_PI": "left_PI"})
        d = Path(tmp) / f.parent.name
        d.mkdir()
        sw.to_csv(d / f.name, index=False)
        shutil.copy(str(f).replace("_walls.csv", "_cell_data.csv"), d)
        a, b = N.measure(f), N.measure(d / f.name)
        rows.append(dict(frame=a["frame"], by_name=a, corrected=b))
        print(f"{a['frame'][-28:]:28s} by name: s_X {a['s_X']:.3f} s_PI {a['s_Q']:.3f} sigma_PIN {a['sigma_PIN']:.3f} | "
              f"corrected sides: s_X {b['s_X']:.3f} s_PI {b['s_Q']:.3f} sigma_PIN {b['sigma_PIN']:.3f}")
for k in ("by_name", "corrected"):
    v = np.array([r[k]["sigma_PIN"] for r in rows])
    print(f"{k}: sigma_PIN median {np.median(v):.3f} (range {v.min():.3f}-{v.max():.3f}); s_X median {np.median([r[k]['s_X'] for r in rows]):.3f}")
json.dump(rows, open(HERE / "out" / "sigma_recheck.json", "w"), indent=1)
