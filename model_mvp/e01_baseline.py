"""E01: which primordium sink rule gives a robust spiral on the growing mesh?"""
from exp import run_grid

if __name__ == "__main__":
    base = dict(t_end=450.0, v_div=1.25)
    variants = {
        "lin+cue":      dict(sink_mode="linear", eta=3.0, A_q=8.0),
        "lin nocue":    dict(sink_mode="linear", eta=3.0, A_q=0.0),
        "cap10 nocue":  dict(sink_mode="cap", eta=10.0, A_cap=10.0, A_q=0.0),
        "cap10+cue":    dict(sink_mode="cap", eta=10.0, A_cap=10.0, A_q=8.0),
        "cap9 nocue":   dict(sink_mode="cap", eta=10.0, A_cap=9.0, A_q=0.0),
        "cap12 nocue":  dict(sink_mode="cap", eta=10.0, A_cap=12.0, A_q=0.0),
    }
    run_grid(variants, seeds=range(1, 9), base=base, out="out/e01.jsonl", show_runs=False)
