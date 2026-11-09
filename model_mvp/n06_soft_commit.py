"""N06 (candidate 1): fix the position of a new primordium later and from more cells.

instant : centre placed the moment the first cell crosses the threshold (reference).
patch   : wait until n connected ring cells are above threshold; centre = centroid of the patch.
track   : reserve the site at first crossing, let it follow the local auxin maximum for tau_c,
          then switch on sink and polarity cue at the tracked position.
"""
import nexp

if __name__ == "__main__":
    V = {"instant (ref)": {}}
    for n in (3, 5, 7):                                  # a 2-cell-wide ring holds about 9 cells within r_patch
        V[f"patch n={n}"] = dict(commit="patch", n_patch=n)
    for tc in (1.0, 2.0, 4.0):
        V[f"track tau_c={tc:g}"] = dict(commit="track", tau_c=tc)
    V["track tau_c=2 r=4"] = dict(commit="track", tau_c=2.0, r_track=4.0)
    nexp.run(V, ["spiral", "lowG+field"], range(1, 11), "out/n06.jsonl")
