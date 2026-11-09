"""E10: pattern type versus ring radius in the sub-critical regime, from three kinds of start."""
from exp import run_grid

OP = dict(v_div=1.25, rho_cz=2.0, rho_prox=2.0, w=3.0, b=2.0, Th=3.3, tau_M=5.0, in_loop=1)

if __name__ == "__main__":
    base = dict(OP, t_end=800.0)
    V = {}
    for rc in (2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0):
        geo = dict(R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0)
        V[f"noise Rc{rc}"] = dict(geo)
        if rc >= 4.0:
            V[f"pair Rc{rc}"] = dict(geo, start="pair", init_frac=1.0)
        if rc >= 6.0:
            V[f"whorl3 Rc{rc}"] = dict(geo, start="whorl3", init_frac=1.0)
    run_grid(V, seeds=range(1, 7), base=base, out="out/e10.jsonl", show_runs=False)
