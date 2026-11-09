"""E05: pattern type versus size of the competent ring and range of the primordium sink.

Outside the ring auxin production is low (2.0) so that only the ring can pattern.
"""
import sys
from exp import run_grid

if __name__ == "__main__":
    base = dict(t_end=800.0, v_div=1.25, rho_cz=2.0, rho_prox=2.0)
    V = {}
    for w in (2.5, 3.0, 3.5):
        for rc in (2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0):
            V[f"w{w} Rc{rc}"] = dict(w=w, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0)
    run_grid(V, seeds=range(1, 7), base=base, out="out/e05.jsonl", show_runs=False)
