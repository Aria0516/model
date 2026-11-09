"""E11a: effect of the integration time in two regimes. E11b: ring radius x sink range grid."""
import sys
from exp import run_grid
from e10_phase_sub import OP

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "tau":
        V = {}
        for rc in (3.5, 4.0):
            for tau in (0.0, 1.0, 2.0, 5.0, 10.0, 20.0):
                V[f"sub Rc{rc} tau{tau}"] = dict(OP, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0, tau_M=tau, in_loop=int(tau > 0))
        hot = dict(v_div=1.25, rho_cz=2.0, rho_prox=2.0, w=3.0, b=3.0, Th=8.5)
        for tau in (0.0, 2.0, 5.0, 10.0):
            V[f"hot Rc4.0 tau{tau}"] = dict(hot, tau_M=tau, in_loop=int(tau > 0))
        run_grid(V, seeds=range(1, 9), base=dict(t_end=800.0), out="out/e11_tau.jsonl", show_runs=False)
    else:
        V = {}
        for w in (2.0, 2.5, 3.0, 3.5, 4.0):
            for rc in (2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 8.0, 9.0):
                V[f"w{w} Rc{rc}"] = dict(OP, w=w, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0)
        run_grid(V, seeds=range(1, 5), base=dict(t_end=800.0), out="out/e11_grid.jsonl", show_runs=False)
