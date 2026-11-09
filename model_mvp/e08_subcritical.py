"""E08: sub-critical ring. The transport feedback amplifies but does not nucleate peaks on its
own; a primordium starts where the smooth, recovering auxin field first crosses the threshold."""
from exp import run_grid

if __name__ == "__main__":
    base = dict(t_end=800.0, v_div=1.25, rho_cz=2.0, rho_prox=2.0, w=3.0)
    V = {}
    for b in (1.8, 2.0, 2.2):
        for th in (3.0, 3.3, 3.6):
            V[f"b{b} Th{th}"] = dict(b=b, Th=th)
    V["b2.0 Th3.3 nocue"] = dict(b=2.0, Th=3.3, A_q=0.0)
    V["b2.0 Th3.3 w2"] = dict(b=2.0, Th=3.3, w=2.0)
    V["b2.0 Th3.3 w4"] = dict(b=2.0, Th=3.3, w=4.0)
    V["b2.0 Th3.3 eta1"] = dict(b=2.0, Th=3.3, eta=1.0)
    run_grid(V, seeds=range(1, 7), base=base, out="out/e08.jsonl", show_runs=False)
