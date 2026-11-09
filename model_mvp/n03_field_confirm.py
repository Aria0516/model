"""N03: confirm the secondary-field result with more seeds and check other pattern types."""
import json
from multiprocessing import Pool

import numpy as np

from n02_secondary_field import one, table

FIELDS = {
    "no field": {},
    "k1.2 r25 life4": dict(k_I=1.2, w_I=25.0, tau_I=4.0),
    "k1.6 r25 life3": dict(k_I=1.6, w_I=25.0, tau_I=3.0),
    "k2.4 r14 life2": dict(k_I=2.4, w_I=14.0, tau_I=2.0),
    "k0.8 r5 life8": dict(k_I=0.8, w_I=5.0, tau_I=8.0),
}
POINTS = {                                              # name: (geometry, seeds)
    "lowG w2.0 Rc5.5": (dict(w=2.0, R_c=5.5), range(1, 17)),
    "lowerG w2.0 Rc7.0": (dict(w=2.0, R_c=7.0), range(1, 9)),
    "spiral w3.0 Rc3.5": (dict(w=3.0, R_c=3.5), range(1, 9)),
    "decussate w3.0 Rc6.0": (dict(w=3.0, R_c=6.0), range(1, 9)),
    "whorl3-seeded w2.0 Rc6.5": (dict(w=2.0, R_c=6.5, start="whorl3", init_frac=1.0), range(1, 9)),
    "whorl3-seeded w3.0 Rc9.0": (dict(w=3.0, R_c=9.0, start="whorl3", init_frac=1.0), range(1, 9)),
}

if __name__ == "__main__":
    jobs = []
    for pn, (geo, seeds) in POINTS.items():
        for fn, fld in FIELDS.items():
            jobs += [(f"{pn} | {fn}", dict(geo, **fld), s) for s in seeds]
    with Pool(28) as pool:
        res = pool.map(one, jobs)
    with open("out/n03.jsonl", "w") as f:
        for r in res:
            f.write(json.dumps(r) + "\n")
    for pn in POINTS:
        print(f"\n=== {pn}")
        table(res, [f"{pn} | {fn}" for fn in FIELDS])
    print("\nspread of P1..P5 (deg) in runs without any permutation motif (paper: 6.7 observed)")
    for pn in ("lowG w2.0 Rc5.5", "spiral w3.0 Rc3.5"):
        for fn in FIELDS:
            rs = [r for r in res if r["name"] == f"{pn} | {fn}" and r.get("jugacy", 9) <= 1 and r.get("f_perm", 1) == 0 and r.get("f_other", 1) <= 0.03]
            if rs:
                m = np.nanmean(np.array([r["rank"] for r in rs]), axis=0)
                print(f"  {pn:18s} {fn:16s} n={len(rs):2d}  ranks 1-6: " + " ".join(f"{v:5.1f}" for v in m) + f"  mean1-5 {np.nanmean(m[:5]):5.1f}  lag1 {np.nanmean([r['lag1'] for r in rs]):+.2f}")
