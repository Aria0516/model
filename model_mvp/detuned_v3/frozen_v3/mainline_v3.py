"""Main line v3 (detuned_v3/PROTOCOL.md): v2 with the regularity-selected settings replaced.

Fixed by literature or data: b = 3 (Smith 2006), no follow-then-fix (commit at threshold), exclusion radius
1.18 w (half maximum of the primordium footprint), secondary field in the Besnard 2014 form (present between
primordium ages a_on and a_off, Gaussian range w_I, raising the threshold by k_rel x threshold).
Everything without an anchor is passed in a sample dict `s` (see PROTOCOL table).
"""
from layer import TwoLayerSim

OP = dict(v_div=1.25, rho_cz=2.0, rho_prox=2.0, w=3.0, b=2.0, Th=3.3, tau_M=5.0, in_loop=1)   # e10_phase_sub.OP (v1 base)
FIXED = dict(b=3.0, commit="instant", field_form="window", k_I=0.0)
READOUT = dict(tau_R=15.0, theta_M=3.0)
A_FREE = 4.0                     # sink-free ring level used by the calibration rule
SRC_OFFSET = 2.0
RC_START, T_RAMP = 2.0, 600.0
HOURS_PER_UNIT = 1.6             # G = 0.23 and 12 h plastochron (Galvan-Ampudia 2020) => 0.019 / h; model gamma 0.03 / unit


def params(rc, rc_end, rin, rho_far, s, **extra):
    rw = s["ring_w"]
    p = dict(OP, w=s["w"], R_c=rc, R_p=rc + rw, R_out=rc_end + 9.0, rho_cz=rin, rho_pz=rin, rho_prox=rin,
             R_src=rc + rw + SRC_OFFSET, rho_far=rho_far, kappa_c=s["kappa_c"], pin_cz=0.2,
             Th=s["theta_rel"] * A_FREE, tau_M=s["tau_M"], eta=s["eta"], A_q=s["A_q"], r_ex=1.18 * s["w"], ring_w=rw,
             k_v=s["k_v"], K_e=s["K_e"], eta2=s["eta2"], D2=None,
             k_rel=s["k_rel"], w_I=s["w_I"], a_on=s["a_on"], a_off=s["a_off"], **FIXED, **READOUT)
    p.update(extra)
    return p


def make(s, rin, rc_end, rho_start, rho_end, seed, t_end=1700.0, ramp=True, **extra):
    rc = RC_START if ramp else rc_end
    p = params(rc, rc_end, rin, rho_start if ramp else rho_end, s, t_end=t_end, mesh_seed=seed, seed=seed, **extra)
    r = dict(T=T_RAMP, rc0=RC_START, rc1=rc_end, rho0=rho_start, rho1=rho_end, ds=SRC_OFFSET) if ramp else None
    return TwoLayerSim(p, r)
