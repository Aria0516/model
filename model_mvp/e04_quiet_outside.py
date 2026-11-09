"""E04: keep the tissue outside the competent ring below the transport-instability threshold.

Linear analysis: at baseline the instability sets in at auxin ~2.7, while the central and outer
zones sit at ~4.5, so they form uncontrolled auxin peaks that compete with primordia.
"""
from exp import run_grid

if __name__ == "__main__":
    base = dict(t_end=450.0, v_div=1.25)
    V = {"baseline (outside 9)": {}}
    for ro in (5.0, 3.0, 2.0):
        V[f"outside={ro}"] = dict(rho_cz=ro, rho_prox=ro)
        V[f"outside={ro} ring4-7"] = dict(rho_cz=ro, rho_prox=ro, R_p=7.0)
        V[f"outside={ro} w3"] = dict(rho_cz=ro, rho_prox=ro, w=3.0)
        V[f"outside={ro} nocue"] = dict(rho_cz=ro, rho_prox=ro, A_q=0.0)
    V["cz9 prox3"] = dict(rho_cz=9.0, rho_prox=3.0)
    V["cz3 prox9"] = dict(rho_cz=3.0, rho_prox=9.0)
    run_grid(V, seeds=range(1, 9), base=base, out="out/e04.jsonl", show_runs=False)
