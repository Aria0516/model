"""N10: two specific mismatches and whether simple adjustments remove them.

levels : auxin level in the competent ring with no primordia, as a function of the polar
         transport coefficient T and of how production is distributed (ring / elsewhere).
         Primordia form without transport if the T = 0 level is above the threshold.
radius : does the Arabidopsis-like pattern survive when ring and sink range are scaled down so
         that initiation happens at ~5 cells (~30 um) instead of ~6.5 cells (~40 um)?
pin    : with production flattened and the threshold placed between the no-transport and the
         with-transport ring level, do we get organs with transport and none without?
"""
import sys

import numpy as np

import nexp
from e10_phase_sub import OP
from lin import analyse
from model import DEFAULT, Sim

if __name__ == "__main__":
    which = sys.argv[1]
    if which == "levels":
        print("ring     production ring/elsewhere   T=0     T=11    T=22.5   ratio(22.5/0)   growth rate of uniform state at the T=22.5 level")
        for rc in (3.5, 5.5):
            for a, b in ((18.0, 2.0), (12.0, 4.0), (9.0, 5.0), (7.0, 6.0), (6.5, 6.5)):
                lev = []
                for T in (0.0, 11.0, 22.5):
                    s = Sim(dict(OP, w=3.0, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0, rho_pz=a, rho_cz=b, rho_prox=b, T=T, Th_rel=0.82, t_end=1.0))
                    lev.append(s.free_level)
                p = dict(DEFAULT); p.update(OP)
                lam = analyse(p, A_level=float(lev[2]))[1]
                print(f"{rc:g}-{rc+2:g}   {a:5.1f} / {b:3.1f}              {lev[0]:5.2f}   {lev[1]:5.2f}   {lev[2]:5.2f}      {lev[2]/lev[0]:5.2f}          {lam:+.2f}")
    elif which == "radius":
        track = dict(commit="track", tau_c=2.0)
        V = {
            "current: ring 5.5-7.5, w 2.0": dict(track),
            "ring 4.5-6.5, w 1.75": dict(track, R_c=4.5, w=1.75),
            "ring 4.0-6.0, w 1.5": dict(track, R_c=4.0, w=1.5),
            "ring 4.0-6.0, w 1.5, r_ex 2": dict(track, R_c=4.0, w=1.5, r_ex=2.0),
            "ring 3.5-5.5, w 1.4": dict(track, R_c=3.5, w=1.4, r_ex=2.0),
            "ring 4.0-5.5 (narrow), w 1.5": dict(track, R_c=4.0, w=1.5, ringw=1.5, r_ex=2.0),
        }
        res = nexp.run(V, ["lowG+field"], range(1, 11), "out/n10_radius.jsonl", t_end=500.0)
        print("\ninitiation radius (cells -> um at 6 um per cell)")
        for n in V:
            rb = [r["Rb"] for r in res if r["name"] == n and "Rb" in r]
            print(f"  {n:32s} {np.mean(rb):4.1f} cells -> {6*np.mean(rb):4.0f} um")
    elif which == "gain":
        # Put the threshold ABOVE the sink-free ring level, so that an initiation needs the transport
        # feedback to amplify a recovering bump (as in Smith 2006), and raise the gain toward the
        # instability threshold so that this amplification exists. Without transport nothing can start.
        V = {"ref b2.0 Th0.82": dict(Th_rel=0.82)}
        for b in (2.3, 2.5, 2.7):
            for th in (1.05, 1.15, 1.3):
                V[f"b{b} Th{th}"] = dict(b=b, Th_rel=th)
        nexp.run(V, ["spiral"], range(1, 9), "out/n10_gain_spiral.jsonl")
        Vt = {k: dict(v, commit="track", tau_c=2.0) for k, v in V.items()}
        nexp.run(Vt, ["lowG+field"], range(1, 9), "out/n10_gain_lowG.jsonl")
        V0 = {k + " T=0": dict(v, T=0.0) for k, v in V.items()}
        res = nexp.run(V0, ["spiral"], range(1, 4), "out/n10_gain_T0.jsonl", t_end=300.0)
        print("\nwithout polar transport, primordia per run:")
        for n in V0:
            print(f"  {n:24s} {[r.get('n', 0) for r in res if r['name'] == n]}")
    elif which == "pin":
        prof = dict(rho_pz=float(sys.argv[2]), rho_cz=float(sys.argv[3]), rho_prox=float(sys.argv[3]))
        thr = float(sys.argv[4])
        V = {}
        for T in (22.5, 11.0, 5.0, 0.0):
            V[f"T={T:g}"] = dict(prof, T=T, Th=thr)
        res = nexp.run(V, ["spiral"], range(1, 9), "out/n10_pin.jsonl", t_end=600.0)
        print("\nprimordia per run:")
        for n in V:
            print(f"  {n:8s} {[r['n'] for r in res if r['name'] == n]}")
