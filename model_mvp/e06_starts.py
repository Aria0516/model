"""E06: are opposite (decussate) and whorled patterns stable when started from a symmetric state?

Dicots start from two opposite cotyledons; Smith et al. 2006 also seeded their runs.
"""
from exp import run_grid

if __name__ == "__main__":
    base = dict(t_end=800.0, v_div=1.25, rho_cz=2.0, rho_prox=2.0, w=3.0, init_frac=1.0)
    V = {}
    for rc in (3.0, 4.0, 5.0, 6.0, 7.0, 8.0):
        V[f"pair Rc{rc}"] = dict(start="pair", R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0)
    for rc in (5.0, 6.0, 7.0, 8.0, 9.0, 10.0):
        V[f"whorl3 Rc{rc}"] = dict(start="whorl3", R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0)
    run_grid(V, seeds=range(1, 7), base=base, out="out/e06.jsonl", show_runs=True)
