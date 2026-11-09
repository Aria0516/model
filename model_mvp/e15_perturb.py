"""E15: which ingredients does the pattern need? In-silico perturbations at the spiral point.

T = 0 mimics loss of polar transport (pin1 / NPA). fb_auxin = 0 removes the auxin -> PIN
feedback while keeping PIN orientation toward primordia. eta = 0 removes the primordium sink.
"""
from exp import run_grid
from e10_phase_sub import OP

if __name__ == "__main__":
    g = dict(OP, R_c=3.5, R_p=5.5, R_out=12.5)
    V = {
        "ref": dict(g),
        "T=0 (no polar transport)": dict(g, T=0.0),
        "T=5": dict(g, T=5.0),
        "T=11": dict(g, T=11.0),
        "T=45": dict(g, T=45.0),
        "no auxin->PIN feedback": dict(g, fb_auxin=0.0),
        "half feedback": dict(g, fb_auxin=0.5),
        "no cue": dict(g, A_q=0.0),
        "no feedback, no cue": dict(g, fb_auxin=0.0, A_q=0.0),
        "no sink": dict(g, eta=0.0),
        "no sink, no cue": dict(g, eta=0.0, A_q=0.0),
        "uniform production": dict(g, rho_cz=18.0, rho_prox=18.0),
    }
    run_grid(V, seeds=range(1, 9), base=dict(t_end=800.0), out="out/e15.jsonl", show_runs=False)
