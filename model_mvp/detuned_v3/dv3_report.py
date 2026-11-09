"""Report for detuned_v3/PROTOCOL.md section 3 (descriptive; every sample is included).

python dv3_report.py
"""
import json
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
SPACE = ["tau_M", "theta_rel", "w", "eta", "A_q", "ring_w", "kappa_c", "k_v", "K_e", "eta2", "rho_in", "k_rel", "w_I", "a_on", "a_off"]
STATS = [("alpha", "mean angle (deg)", 137.5), ("nc", "non-canonical", 0.15), ("spread", "P1-P5 spread (deg)", 6.7),
         ("gap_cv", "interval CV", 0.22), ("co25", "co-initiation <0.25 gap", None), ("co50", "co-initiation <0.5 gap", 0.28),
         ("hours", "plastochron (h)", 12.0), ("G", "G", 0.23), ("r_um", "initiation radius (um)", 29.0)]
BANDS = dict(alpha=(135, 140), nc=(0.09, 0.21), spread=(4.0, 9.4), gap_cv=(0.13, 0.31), hours=(10, 14), G=(0.18, 0.28), r_um=(26, 33))

samples = json.load(open(OUT / "samples.json"))
cal = {int(k): v for k, v in json.load(open(OUT / "calib.json")).items()}
res = json.load(open(OUT / "runs.json"))
runs = [r for r in res if r["T"] is None]
ctl = {r["i"]: r["n"] for r in res if r["T"] is not None}
r0 = {i: cal[i]["ratio_T0"] < samples[i]["theta_rel"] for i in cal}
analysed = [r for r in runs if "alpha" in r]

print(f"samples {len(samples)}, runs {len(runs)} (2 seeds each); R0 holds in {sum(r0.values())}/{len(r0)} samples; "
      f"T=0 control produced primordia in {sum(v > 0 for v in ctl.values())}/{len(ctl)} samples "
      f"(of which R0 fails: {sum(ctl[i] > 0 and not r0[i] for i in ctl)})")

print("\n1-3. outcome classes over all runs")
cls = {"regular spiral": 0, "other regular": 0, "irregular": 0, "too few primordia (<12)": 0}
for r in runs:
    p = r.get("pattern", "")
    if p in ("stalled", "none"):
        cls["too few primordia (<12)"] += 1
    elif p.endswith("~"):
        cls["irregular"] += 1
    elif p == "spiral":
        cls["regular spiral"] += 1
    else:
        cls["other regular"] += 1
for k, v in cls.items():
    print(f"   {k:26s} {v:4d} / {len(runs)}  ({100 * v / len(runs):.0f}%)")
types = {}
for r in analysed:
    types[r["pattern"]] = types.get(r["pattern"], 0) + 1
print("   pattern labels:", ", ".join(f"{k} {v}" for k, v in sorted(types.items(), key=lambda x: -x[1])))

print("\n   statistic                  median   IQR              range            data    in data band")
inband_all = np.ones(len(analysed), bool)
for key, name, data in STATS:
    v = np.array([r[key] for r in analysed if r.get(key) is not None and np.isfinite(r[key])], float)
    if not len(v):
        continue
    band = BANDS.get(key)
    if band:
        mask = np.array([(r.get(key) is not None) and band[0] <= r[key] <= band[1] for r in analysed])
        inband_all &= mask
        frac = f"{mask.mean() * 100:5.1f}% ({band[0]}-{band[1]})"
    else:
        frac = ""
    print(f"   {name:26s} {np.median(v):7.3f}  {np.quantile(v, .25):7.3f}-{np.quantile(v, .75):<7.3f}  {v.min():7.3f}-{v.max():<7.3f}  "
          f"{'' if data is None else data:<6}  {frac}")
print(f"   runs inside every band at once: {inband_all.sum()} / {len(analysed)} analysed runs")

base = [r for r in json.load(open(HERE.parent / "calib_v2" / "out" / "runs.json")) if r["name"] == "calibrated"]
print("\n5. main line v2 (calibrated geometry), for comparison: angle {:.1f}, non-canonical {:.0%}, spread {:.1f}, interval CV {:.2f}, "
      "G {:.2f}, regular {}/{}".format(np.median([r["alpha"] for r in base]), 1 - np.median([r["f_alpha"] for r in base]),
                                      np.median([r["spread"] for r in base]), np.median([r["gap_cv"] for r in base]),
                                      np.median([r["G"] for r in base]), sum(not r["pattern"].endswith("~") for r in base), len(base)))

print("\n4. Spearman rank correlation, sampled parameter vs statistic (analysed runs; |rho| >= 0.3 marked *)")
print("   " + "".join(f"{k:>9s}" for k, _, _ in STATS))
for prm in SPACE:
    line = []
    for key, _, _ in STATS:
        x = [samples[r["i"]][prm] for r in analysed if r.get(key) is not None and np.isfinite(r[key])]
        y = [r[key] for r in analysed if r.get(key) is not None and np.isfinite(r[key])]
        rho = spearmanr(x, y).statistic if len(x) > 10 else np.nan
        line.append(f"{rho:8.2f}{'*' if abs(rho) >= 0.3 else ' '}")
    print(f"   {prm:9s}" + "".join(line))
