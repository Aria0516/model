"""Held-out tests on the frozen model (see PROTOCOL.md). Nothing in the model is changed here.

python run_heldout.py H1 | H4 | H5 | H6 | H7 | H9 | all
"""
import hashlib
import json
import math
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN = HERE.parent / "frozen_v1"
sys.path.insert(0, str(FROZEN))                         # import the frozen model only

import numpy as np  # noqa: E402

import analysis  # noqa: E402
import noise_tools  # noqa: E402
from model import Sim  # noqa: E402
from nexp import ARABIDOPSIS_LIKE  # noqa: E402

OUT = HERE / "out"
T_END = 600.0


def check_frozen():
    for line in (FROZEN / "MANIFEST.sha256").read_text().splitlines():
        h, name = line.split()
        assert hashlib.sha256((FROZEN / name).read_bytes()).hexdigest() == h, f"{name} differs from the frozen version"
    import model
    assert Path(model.__file__).resolve().parent == FROZEN, "model was not imported from frozen_v1"


def signed_angles(log):
    th = np.degrees(np.arctan2([l[2] for l in log], [l[1] for l in log])) % 360
    return np.diff(th) % 360


def summary(sim):
    s = analysis.summarize(sim.log, sim.p["gamma"])
    s["rank"] = noise_tools.rank_spread(sim.log)
    d = signed_angles(sim.log)
    k = len(d) // 3
    s["ccw"] = bool((d[k:] < 180).mean() >= 0.5) if len(d) > 6 else None
    return s


# ---- generic run -------------------------------------------------------------
def plain(job):
    tag, over, seed = job
    sim = Sim(dict(ARABIDOPSIS_LIKE, t_end=T_END, mesh_seed=seed, seed=seed, **over)).run()
    s = summary(sim)
    s.update(tag=tag, seed=seed, angles=np.round(signed_angles(sim.log), 1).tolist(), times=[round(l[0], 2) for l in sim.log])
    if sim.dg_n:
        s.update(prof=(sim.dg_prof / sim.dg_n).round(3).tolist(), pin_in_free=(sim.dg_in_free / sim.dg_n).round(3).tolist())
    return s


# ---- H1: switch off the sink of one young primordium -------------------------------
class DrainOff(Sim):
    """At the first primordium fixed after t_start, set its sink to zero (cue kept)."""

    def __init__(self, params, t_start, treat):
        self._t_start, self._treat, self.target = t_start, treat, None
        super().__init__(params)

    def _geometry(self, first=False):
        super()._geometry(first)
        if self.target is None and self.t >= self._t_start:
            new = [q for q in self.prim if q["tc"] >= self._t_start]
            if new:
                q = min(new, key=lambda z: z["tc"])
                self.target = (q["id"], self.t)
                if self._treat:
                    q["sink"] = 0.0


def h1(job):
    seed, treat = job
    sim = DrainOff(dict(ARABIDOPSIS_LIKE, t_end=T_END, mesh_seed=seed, seed=seed, track=1), 300.0, treat).run()
    pid, t0 = sim.target
    tr = np.array(sim.track[pid])                       # t, radius, A, M, R at the primordium centre
    d = signed_angles(sim.log)
    s = analysis.summarize(sim.log, sim.p["gamma"])
    gap = s.get("gap_mean", float("nan"))
    win = (tr[:, 0] >= t0) & (tr[:, 0] < t0 + gap)
    ccw = bool((d[len(d) // 3:] < 180).mean() >= 0.5)
    alpha_signed = s.get("alpha", float("nan")) if ccw else 360.0 - s.get("alpha", float("nan"))
    return dict(seed=seed, treat=treat, pid=pid, t0=t0, gap=gap, A_mean=float(tr[win, 2].mean()), A_max=float(tr[win, 2].max()),
                angles_after=np.round(d[pid:pid + 10], 1).tolist(),         # d[pid] = angle from the target to the next primordium
                alpha=alpha_signed, pattern=s["pattern"], f_alpha=s.get("f_alpha"))


def run_h1():
    with Pool(28) as pool:
        res = pool.map(h1, [(s, t) for s in range(1, 17) for t in (False, True)])
    json.dump(res, open(OUT / "H1.json", "w"))
    ctrl = {r["seed"]: r for r in res if not r["treat"]}; trt = {r["seed"]: r for r in res if r["treat"]}
    seeds = sorted(ctrl)
    ratio = np.array([trt[s]["A_mean"] / ctrl[s]["A_mean"] for s in seeds])
    print("H1  sink of one young primordium switched off (16 paired runs)")
    print(f"  a. auxin at that primordium over the next interval, treated/control: median {np.median(ratio):.2f} "
          f"(range {ratio.min():.2f}-{ratio.max():.2f}); > 1.2 in {(ratio > 1.2).sum()}/16")
    wrap = lambda x: (np.asarray(x) + 180) % 360 - 180
    shift = np.array([[abs(wrap(trt[s]["angles_after"][k] - ctrl[s]["angles_after"][k])) for k in range(8)] for s in seeds
                      if len(trt[s]["angles_after"]) >= 8 and len(ctrl[s]["angles_after"]) >= 8])
    print("  b. |treated - control| of the k-th angle after the treated primordium, mean over runs (deg):")
    print("     k=1..8: " + " ".join(f"{v:5.1f}" for v in shift.mean(0)) + f"   (n={len(shift)})")
    dev = lambda rr, lo, hi: np.mean([np.abs(wrap(np.array(rr[s]["angles_after"][lo:hi]) - rr[s]["alpha"])).mean()
                                      for s in seeds if len(rr[s]["angles_after"]) >= hi])
    dt, dc = dev(trt, 3, 8), dev(ctrl, 3, 8)
    reg = sum(not trt[s]["pattern"].endswith("~") for s in seeds)
    print(f"  c. mean deviation from the dominant angle at k=4..8: treated {dt:.1f}, control {dc:.1f} (ratio {dt/dc:.2f}); "
          f"treated runs ending as a regular pattern: {reg}/16; control: {sum(not ctrl[s]['pattern'].endswith('~') for s in seeds)}/16")
    a = bool(np.median(ratio) > 1.2); b = bool(shift.mean(0)[:2].max() >= 15.0); c = bool((dt / dc <= 1.5) and (reg / 16 >= 0.75))
    met = int(a) + int(b) + int(c)                      # plain ints: numpy booleans would add as logical OR
    print(f"  criteria met: a={a} b={b} c={c}  ->  {'PASS' if met == 3 else 'PARTIAL' if met == 2 else 'FAIL'}")


def table(res, tags):
    for t in tags:
        rs = [r for r in res if r["tag"] == t and r.get("pattern") != "none"]
        n_all = len([r for r in res if r["tag"] == t])
        if not rs:
            print(f"  {t:22s} no primordia in {n_all} runs"); continue
        g = lambda k: float(np.mean([r[k] for r in rs]))
        reg = sum(not r["pattern"].endswith("~") for r in rs)
        pats = {}
        for r in rs:
            pats[r["pattern"]] = pats.get(r["pattern"], 0) + 1
        print(f"  {t:22s} angle {np.median([r['alpha'] for r in rs]):6.1f}  interval {g('gap_mean'):5.2f}  non-canonical {100*(1-g('f_alpha')):4.0f}%  "
              f"intervalCV {g('gap_cv'):.2f}  short {g('frac_short'):.2f}  Rb_sd {g('Rb_sd'):.2f}  regular {reg}/{len(rs)}  primordia/run {g('n'):.0f}  {pats}")


def run_simple(name, cases, seeds):
    with Pool(28) as pool:
        res = pool.map(plain, [(t, o, s) for t, o in cases.items() for s in seeds])
    json.dump(res, open(OUT / f"{name}.json", "w"))
    return res


if __name__ == "__main__":
    check_frozen()
    OUT.mkdir(exist_ok=True)
    which = sys.argv[1]
    todo = ["H1", "H4", "H5", "H6", "H7", "H9"] if which == "all" else [which]
    for w in todo:
        print(f"\n===== {w}")
        if w == "H1":
            run_h1()
        elif w == "H4":
            res = run_simple("H4", {"reference": {}}, range(1, 49))
            ok = [r for r in res if r["ccw"] is not None]
            k = sum(r["ccw"] for r in ok); n = len(ok)
            p = sum(math.comb(n, i) for i in range(n + 1) if abs(i - n / 2) >= abs(k - n / 2)) / 2 ** n
            print(f"H4  handedness: {k} counter-clockwise, {n - k} clockwise of {n}; two-sided binomial p = {p:.2f}  ->  {'PASS' if p > 0.05 else 'FAIL'}")
            table(res, ["reference"])
        elif w == "H5":
            res = run_simple("H5", {"opposite-pair start": dict(start="pair", init_frac=1.0)}, range(1, 17))
            table(res, ["opposite-pair start"])
            reg = sum(not r["pattern"].endswith("~") and r["pattern"] in ("spiral", "lucas") for r in res)
            settle = []
            for r in res:
                a = np.array(r["angles"]); al = r.get("alpha", 137.5)
                f = np.minimum(a, 360 - a)
                bad = np.where(np.abs(f - al) > 20)[0]
                settle.append(int(bad.max() + 2) if len(bad) and bad.max() < len(a) - 5 else (1 if not len(bad) else None))
            ss = [x for x in settle if x is not None]
            print(f"H5  regular spiral in {reg}/16; first six angles (folded, mean over runs): "
                  + " ".join(f"{v:.0f}" for v in np.mean([np.minimum(r['angles'][:6], 360 - np.array(r['angles'][:6])) for r in res], axis=0))
                  + f"; primordia needed before angles stay within 20 deg: median {np.median(ss) if ss else float('nan'):.0f} (n={len(ss)})"
                  + f"  ->  {'PASS' if reg >= 12 else 'FAIL'}")
        elif w == "H6":
            res = run_simple("H6", {"with field": {}, "field off": dict(k_I=0.0)}, range(1, 17))
            table(res, ["with field", "field off"])
            A = [r for r in res if r["tag"] == "with field" and r["pattern"] != "none"]; B = [r for r in res if r["tag"] == "field off" and r["pattern"] != "none"]
            m = lambda rs, k: float(np.mean([r[k] for r in rs]))
            da = abs(np.median([r["alpha"] for r in B]) - np.median([r["alpha"] for r in A]))
            dg = abs(m(B, "gap_mean") / m(A, "gap_mean") - 1)
            ncA, ncB = 1 - m(A, "f_alpha"), 1 - m(B, "f_alpha")
            a = bool(da < 5); b = bool(dg < 0.2); c = bool((ncB >= 1.5 * ncA) and (m(B, "f_alpha") >= 0.5)); d = bool((m(A, "Rb_sd") < 1) and (m(B, "Rb_sd") < 1))
            print(f"H6  a. angle change {da:.1f} deg ({a})  b. interval change {100*dg:.0f}% ({b})  "
                  f"c. non-canonical {100*ncA:.0f}% -> {100*ncB:.0f}%, canonical majority kept: {m(B, 'f_alpha') >= 0.5} ({c})  d. radius sd < 1 cell ({d})"
                  f"  ->  {'PASS' if a and b and c and d else 'PARTIAL' if (int(a) + int(b) + int(c) + int(d)) == 3 else 'FAIL'}")
        elif w == "H7":
            res = run_simple("H7", {"no polar transport": dict(T=0.0)}, range(1, 9))
            n = [r["n"] for r in res]
            table(res, ["no polar transport"])
            print(f"H7  primordia per run without polar transport: {n}  ->  {'PASS' if max(n) == 0 else 'FAIL'}")
        elif w == "H9":
            res = run_simple("H9", {"reference": dict(diag=1)}, range(1, 9))
            prof = np.mean([r["prof"] for r in res], axis=0); pin = np.mean([r["pin_in_free"] for r in res], axis=0)
            cz, ring = prof[0:5].mean(), prof[5:8].mean()
            pin_ring, pin_out = pin[5:8].mean(), pin[8:12].mean()
            print(f"H9  mean auxin: central zone {cz:.2f}, competent ring {ring:.2f} (ratio {cz/ring:.2f}); "
                  f"PIN inward index: ring {pin_ring:+.2f}, next 4 cells outward {pin_out:+.2f}"
                  f"  ->  {'PASS' if cz >= ring and pin_ring > 0.2 and pin_out > 0.2 else 'FAIL'}")
