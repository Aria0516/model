"""N07 (candidate 3): let the primordium sink change with age.

grow  : the footprint enlarges as the primordium moves out (grow=1 means like the surrounding tissue).
fade  : sink and polarity cue decay once the primordium has moved out by a radial factor f.
Ages are given as radial factors so that the two operating points are treated alike.
"""
import math

import nexp

GAMMA = 0.03
age = lambda f: math.log(f) / GAMMA

if __name__ == "__main__":
    V = {"constant (ref)": {}}
    V["grow 0.5 cap x2"] = dict(w_grow=0.5, w_cap=2.0)
    V["grow 1.0 cap x2"] = dict(w_grow=1.0, w_cap=2.0)
    V["grow 1.0 cap x3"] = dict(w_grow=1.0, w_cap=3.0)
    V["grow 1.0 cap x2, start 0.8w"] = dict(w_grow=1.0, w_cap=2.0, wscale=0.8)
    for f in (1.3, 1.6, 2.0):
        V[f"fade after x{f}"] = dict(sink_age_off=age(f), cue_age_off=age(f), sink_tau=4.0, cue_tau=4.0)
    V["sink fades x1.6, cue stays"] = dict(sink_age_off=age(1.6), sink_tau=4.0)
    V["grow 1.0 cap x2 + fade x2.0"] = dict(w_grow=1.0, w_cap=2.0, sink_age_off=age(2.0), cue_age_off=age(2.0), sink_tau=4.0, cue_tau=4.0)
    # 'wscale' is applied relative to each point's own w
    for name, o in V.items():
        if "wscale" in o:
            o.pop("wscale"); o["_wscale"] = 0.8
    nexp.run(V, ["spiral", "lowG+field"], range(1, 11), "out/n07.jsonl")
