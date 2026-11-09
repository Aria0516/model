"""E14: can three-membered whorls be maintained? Seeded with three primordia at 120 degrees."""
from exp import run_grid
from e10_phase_sub import OP

if __name__ == "__main__":
    V = {}
    for w, rcs in ((2.0, (5.0, 5.5, 6.0, 6.5, 7.0)), (2.5, (6.5, 7.5, 8.5)), (3.0, (8.0, 9.0, 10.0, 11.0))):
        for rc in rcs:
            g = dict(OP, w=w, R_c=rc, R_p=rc + 2.0, R_out=rc + 9.0, start="whorl3", init_frac=1.0)
            V[f"w{w} Rc{rc}"] = dict(g)
            V[f"w{w} Rc{rc} avg"] = dict(g, avg_nb=1)
    run_grid(V, seeds=range(1, 7), base=dict(t_end=800.0), out="out/e14.jsonl", show_runs=False)
