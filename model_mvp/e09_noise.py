"""E09: what reduces positional noise in the sub-critical regime?

Candidates: threshold read from a founder-cell group (spatial average), from a leaky temporal
integral of auxin, a more regular mesh, or slower/faster chemistry relative to growth.
"""
from exp import run_grid

if __name__ == "__main__":
    base = dict(t_end=800.0, v_div=1.25, rho_cz=2.0, rho_prox=2.0, w=3.0, b=2.0, Th=3.3)
    V = {
        "ref": {},
        "avg1": dict(avg_nb=1),
        "avg2": dict(avg_nb=2),
        "avg1 Th3.2": dict(avg_nb=1, Th=3.2),
        "memory tau2": dict(tau_M=2.0, in_loop=1),
        "memory tau5": dict(tau_M=5.0, in_loop=1),
        "memory tau5 avg1": dict(tau_M=5.0, in_loop=1, avg_nb=1),
        "lloyd0.6": dict(lloyd=0.6),
        "lloyd0.6 avg1": dict(lloyd=0.6, avg_nb=1),
        "w4": dict(w=4.0),
        "w4 avg1": dict(w=4.0, avg_nb=1),
        "w4 avg2": dict(w=4.0, avg_nb=2),
        "w4 memory5 avg1": dict(w=4.0, tau_M=5.0, in_loop=1, avg_nb=1),
        "gamma0.015": dict(gamma=0.015, t_end=1600.0),
    }
    run_grid(V, seeds=range(1, 9), base=base, out="out/e09.jsonl", show_runs=False)
