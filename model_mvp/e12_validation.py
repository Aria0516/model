"""E12: do the spiral and decussate results survive changes of numerical and bookkeeping choices?"""
from exp import run_grid
from e10_phase_sub import OP

if __name__ == "__main__":
    V = {}
    for tag, rc in (("spiral", 3.5), ("decussate", 6.0)):
        g = dict(OP, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0)
        V[f"{tag} ref"] = dict(g)
        V[f"{tag} dt/2"] = dict(g, dt=0.005, n_geo=50)
        V[f"{tag} geo x2.5 finer"] = dict(g, n_geo=10)
        V[f"{tag} r_ex=2"] = dict(g, r_ex=2.0)
        V[f"{tag} r_ex=4.5"] = dict(g, r_ex=4.5)
        V[f"{tag} domain +4"] = dict(g, R_out=rc + 13.0)
        V[f"{tag} cells 30% smaller"] = dict(g, v_div=0.875)
        V[f"{tag} no dilution"] = dict(g, dilution=0)
        V[f"{tag} no cue"] = dict(g, A_q=0.0)
        V[f"{tag} founder avg"] = dict(g, avg_nb=1)
    run_grid(V, seeds=range(1, 9), base=dict(t_end=800.0), out="out/e12.jsonl", show_runs=False)
