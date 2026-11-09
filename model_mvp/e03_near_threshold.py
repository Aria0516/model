"""E03: operate the transport feedback near its instability threshold.

There only the high-production ring is (weakly) unstable, so competence emerges from the
auxin level, and spacing is selected collectively over ~8-10 cells instead of being seeded
by cell-scale noise.
"""
from exp import run_grid

if __name__ == "__main__":
    base = dict(t_end=450.0, v_div=1.25)
    V = {}
    for tag, op in (("D10", dict(D=10.0)), ("T12", dict(T=12.0)), ("b2.2", dict(b=2.2)), ("D8", dict(D=8.0))):
        for th in (7.0, 7.5, 8.0):
            V[f"{tag} Th{th} sink+cue"] = dict(op, Th=th)
            V[f"{tag} Th{th} sink"] = dict(op, Th=th, A_q=0.0)
            V[f"{tag} Th{th} passive"] = dict(op, Th=th, A_q=0.0, eta=0.0)
    run_grid(V, seeds=range(1, 7), base=base, out="out/e03.jsonl", show_runs=False)
