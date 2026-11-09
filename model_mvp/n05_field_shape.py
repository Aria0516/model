"""N05: a secondary field shaped like the one Besnard et al. 2014 describe.

They report AHP6 switching on about one plastochron after DR5 and forming local fields around
primordia. Here the field rises with time constant ~1 plastochron (8 model time units at this
point), has a range of a few cells, and lasts 2-4 plastochrons. Compared with the immediate,
ring-wide, short-lived field of N02/N03.
"""
import json
from multiprocessing import Pool

from n02_secondary_field import one, table

if __name__ == "__main__":
    geo = dict(w=2.0, R_c=5.5)
    V = {"no field": dict(geo), "immediate ring-wide (k1.2 r25 life4)": dict(geo, k_I=1.2, w_I=25.0, tau_I=4.0)}
    for k in (1.5, 3.0):
        for wI in (4.0, 6.0, 9.0):
            for life in (16.0, 32.0):
                V[f"delayed k{k} range{wI:g} life{life:g}"] = dict(geo, k_I=k, w_I=wI, tau_I=life, rise_I=8.0)
    jobs = [(n, o, s) for n, o in V.items() for s in range(1, 11)]
    with Pool(28) as pool:
        res = pool.map(one, jobs)
    with open("out/n05.jsonl", "w") as f:
        for r in res:
            f.write(json.dumps(r) + "\n")
    table(res, list(V))
