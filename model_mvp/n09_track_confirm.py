"""N09: confirm the 'follow the maximum, then fix the position' result (track mode of N06).

a  more seeds at the Arabidopsis-like point; numerical and bookkeeping checks; other spiral points
b  without the secondary field the delayed sink lets several sites start together:
   does that give regular whorls at larger rings?
"""
import sys

import nexp

if __name__ == "__main__":
    which = sys.argv[1]
    T2 = dict(commit="track", tau_c=2.0)
    if which == "a1":
        V = {"instant": {}, "track tau_c=1": dict(commit="track", tau_c=1.0), "track tau_c=2": dict(T2)}
        nexp.run(V, ["lowG+field"], range(1, 17), "out/n09_a1.jsonl")
    elif which == "a2":
        V = {
            "track tau_c=2": dict(T2),
            "time step / 2": dict(T2, dt=0.005, n_geo=50),
            "geometry update x2.5 finer": dict(T2, n_geo=10),
            "exclusion radius 2": dict(T2, r_ex=2.0),
            "exclusion radius 4.5": dict(T2, r_ex=4.5),
            "tracking radius 2.0": dict(T2, r_track=2.0),
            "tracking radius 3.0": dict(T2, r_track=3.0),
            "no memory (tau_M=0)": dict(T2, tau_M=0.0, in_loop=0),
        }
        nexp.run(V, ["lowG+field"], range(1, 9), "out/n09_a2.jsonl")
    elif which == "a3":
        V = {"instant": {}, "track tau_c=2": dict(T2)}
        nexp.run(V, ["spiral+field", "lowerG+field"], range(1, 11), "out/n09_a3.jsonl")
    elif which == "b":
        V = {"instant": {}, "track tau_c=2": dict(T2), "track tau_c=4": dict(commit="track", tau_c=4.0)}
        nexp.run(V, ["ring5", "ring6", "ring7", "ring8", "ring9"], range(1, 9), "out/n09_b.jsonl", t_end=700.0)
