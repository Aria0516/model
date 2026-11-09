"""Main line v2, frozen 2026-10-14: ring auxin supplied by polar transport (structural change 1)
plus an inner layer under the epidermis (structural change 2).

Every value is written out here so that this directory does not depend on the development tree.
Where each value comes from: README.md in this directory.

    from mainline import make
    sim = make(rin=2.0, seed=1).run()
"""
from layer import TwoLayerSim

OP = dict(v_div=1.25, rho_cz=2.0, rho_prox=2.0, w=3.0, b=2.0, Th=3.3, tau_M=5.0, in_loop=1)   # e10_phase_sub.OP
FIELD = dict(k_I=1.2, w_I=25.0, tau_I=4.0)                                                   # nexp.FIELD
TRACK = dict(commit="track", tau_c=2.0, **FIELD)
READOUT = dict(tau_R=15.0, theta_M=3.0)                   # passive DR5-like read-out, no effect on the dynamics
LAYER = dict(k_v=0.3, K_e=3.0, eta2=3.0)
KAPPA_C, SRC_OFFSET, W = 1.0, 2.0, 2.0
RC_START, RC_END, T_RAMP = 2.0, 5.5, 600.0
TH = 0.82 * 4.0                                           # 0.82 x sink-free ring level
RHO_IN = (0.0, 2.0)                                       # local production in the meristem; both are reported
# peripheral production giving a sink-free ring level of 4.0 (v3_layer/out/calib.json, k_v = 0.3)
RHO_FAR = {(2.0, 0.0): 1.781312666131434, (5.5, 0.0): 10.984395278984925,
           (2.0, 2.0): 1.185238348024056, (5.5, 2.0): 6.764565315506091}


def params(rc, rin, **extra):
    p = dict(OP, w=W, R_c=rc, R_p=rc + 2.0, R_out=RC_END + 9.0, rho_cz=rin, rho_pz=rin, rho_prox=rin,
             R_src=rc + 2.0 + SRC_OFFSET, rho_far=RHO_FAR[(rc, rin)], kappa_c=KAPPA_C, pin_cz=0.2, Th=TH,
             **TRACK, **READOUT, **LAYER)
    p.update(extra)
    return p


def make(rin=2.0, seed=1, t_end=1700.0, ramp=True, **extra):
    """ramp=True: the ring grows from radius 2.0 to 5.5 over 600, then stays (the start used in all v2/v3 studies)."""
    rc = RC_START if ramp else RC_END
    p = params(rc, rin, t_end=t_end, mesh_seed=seed, seed=seed, **extra)
    r = dict(T=T_RAMP, rc0=RC_START, rc1=RC_END, rho0=RHO_FAR[(RC_START, rin)], rho1=RHO_FAR[(RC_END, rin)],
             ds=SRC_OFFSET) if ramp else None
    return TwoLayerSim(p, r)
