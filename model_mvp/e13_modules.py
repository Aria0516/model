"""E13: modules taken from Galvan-Ampudia 2020 / Barbier de Reuille 2006, added one at a time.

M2  central zone as a reservoir (low PIN export, optional own production) and a tissue-scale
    centripetal PIN bias.
M3  primordia stop draining and start producing auxin once they have moved out by a given
    radial factor (stand-in for 'P3-P5 are sources'; expressed geometrically because the
    plastochron ratio differs from Arabidopsis in this regime).
M4  DR5-like read-out downstream of the memory variable (passive; does not feed back).
"""
import math
import sys
from exp import run_grid
from e10_phase_sub import OP

if __name__ == "__main__":
    rc, gam = 4.0, 0.03
    g = dict(OP, R_c=rc, R_p=rc + 2.0, R_out=17.0, diag=1)
    age = lambda f: math.log(f) / gam                 # time for a primordium to move out by factor f
    m3 = dict(sink_age_off=age(1.6), cue_age_off=age(1.6), sink_tau=5.0, cue_tau=5.0, src_age_on=age(2.0), src_tau=5.0)
    V = {
        "ref": dict(g),
        "M2 pin_cz0.3": dict(g, pin_cz=0.3),
        "M2 pin_cz0.3 rho_cz6": dict(g, pin_cz=0.3, rho_cz=6.0),
        "M2 kappa_c0.5": dict(g, kappa_c=0.5),
        "M2 kappa_c1.0": dict(g, kappa_c=1.0),
        "M2 pin_cz0.3+kc0.5": dict(g, pin_cz=0.3, kappa_c=0.5),
        "M3 sink off only": dict(g, **dict(m3, rho_src=0.0)),
        "M3 src6": dict(g, **dict(m3, rho_src=6.0)),
        "M3 src12": dict(g, **dict(m3, rho_src=12.0)),
        "M3 src12 + kc0.5": dict(g, kappa_c=0.5, **dict(m3, rho_src=12.0)),
        "M2+M3 full": dict(g, pin_cz=0.3, kappa_c=0.5, **dict(m3, rho_src=12.0)),
        "M2+M3 full kc1.0": dict(g, pin_cz=0.3, kappa_c=1.0, **dict(m3, rho_src=12.0)),
        "M4 tauR5": dict(g, tau_R=5.0, theta_M=3.0, track=1),
        "M4 tauR15": dict(g, tau_R=15.0, theta_M=3.0, track=1),
    }
    run_grid(V, seeds=range(1, 7), base=dict(t_end=800.0), out="out/e13.jsonl", show_runs=False)
