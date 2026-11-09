"""E16: does a Smith-type capped sink (only the excess above A_cap is exported) keep primordia as
persistent auxin maxima, as in the data, while preserving the pattern? With read-out tracking."""
from exp import run_grid
from e10_phase_sub import OP

if __name__ == "__main__":
    g = dict(OP, R_c=3.5, R_p=5.5, R_out=12.5, track=1, tau_R=15.0, theta_M=3.0)
    V = {"linear sink (ref)": dict(g)}
    for cap in (2.5, 3.0, 3.5, 4.0):
        V[f"cap{cap}"] = dict(g, sink_mode="cap", eta=10.0, A_cap=cap)
    V["cap3.0 nocue"] = dict(g, sink_mode="cap", eta=10.0, A_cap=3.0, A_q=0.0)
    V["cap3.5 Rc4"] = dict(g, sink_mode="cap", eta=10.0, A_cap=3.5, R_c=4.0, R_p=6.0, R_out=13.0)
    V["linear eta1"] = dict(g, eta=1.0)
    V["linear eta0.5"] = dict(g, eta=0.5)
    res = run_grid(V, seeds=range(1, 7), base=dict(t_end=800.0), out="out/e16.jsonl", show_runs=False)
    import numpy as np
    print("\nread-out (tau_R = 15, threshold 3.0): lag between auxin peak at a primordium and DR5-like signal reaching 0.5")
    for name in V:
        rs = [r for r in res if r["name"].split("|")[0] == name]
        lag = [r["dr5_lag"] for r in rs if "dr5_lag" in r]
        tp = np.mean([r["gap_mean"] for r in rs if "gap_mean" in r])
        nl = sum(r.get("n_lag", 0) for r in rs)
        print(f"  {name:20s} primordia switching on: {nl:4d}  median lag: {np.median(lag) if lag else float('nan'):6.1f}  "
              f"interval: {tp:5.1f}  lag/interval: {(np.median(lag) / tp) if lag else float('nan'):.2f}")
