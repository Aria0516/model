"""Report for A1 (PROTOCOL.md). Written before any run finished.

python report_a1.py      # reads out/events_*.json; writes out/report.txt, out/summary.json, out/fig_A1_*.png/pdf
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import observables as O  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

OUT = HERE / "out"
V3 = HERE.parent / "detuned_v3"
SAMPLES = json.load(open(V3 / "out" / "samples.json"))
CAL = {int(k): v for k, v in json.load(open(V3 / "out" / "calib.json")).items()}
METRICS = [("coinit_org", 0.05, "Co-initiation"), ("gap_cv", 0.05, "Interval CV"),
           ("spread", 2.0, "P1-P5 spread (°)"), ("alpha", 2.0, "Mean divergence (°)")]
TYPE_MARGIN = 0.05
NB = 2000


def run_class(ev):
    if ev["stalled"]:
        return "stalled"
    return "normal" if ev["n"] >= max(O.MIN_EVENTS.values()) else "insufficient"


def boot(vals, rng):
    vals = np.asarray(vals, float)
    idx = rng.integers(0, len(vals), (NB, len(vals)))
    m = vals[idx].mean(1)
    return float(vals.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def decide(lo, hi, margin):
    if -margin <= lo and hi <= margin:
        return "negligible"
    if lo > margin or hi < -margin:
        return "substantial"
    return "insufficient evidence"


def decide_type(lo, hi):
    if hi <= TYPE_MARGIN:
        return "negligible"
    if lo > TYPE_MARGIN:
        return "substantial"
    return "insufficient evidence"


def main():
    ev = {}
    for f in sorted(OUT.glob("events_*.json")):
        d = json.load(open(f))
        ev[(d["cond"], d["i"], d["seed"])] = O.evaluate(d["log"], gamma=d["gamma"])
    sets = sorted({i for (_, i, _) in ev})
    complete = [i for i in sets if all((c, i, s) in ev for c in ("on", "off") for s in (1, 2))]
    r0 = {i: CAL[i]["ratio_T0"] < SAMPLES[i]["theta_rel"] for i in complete}
    lines = [f"A1 paired ablation: {len(complete)} complete parameter sets ({len(ev)} runs)"]
    summary = {}
    rng = np.random.default_rng(0)
    for label, members in (("all", complete), ("R0 holds (transport-limited)", [i for i in complete if r0[i]]),
                           ("R0 fails", [i for i in complete if not r0[i]])):
        lines.append(f"\n== {label}: {len(members)} parameter sets")
        res = {}
        for k, margin, name in METRICS:
            per, used = [], 0
            for i in members:
                ds = [ev[("off", i, s)][k] - ev[("on", i, s)][k] for s in (1, 2)
                      if ev[("on", i, s)]["status"][k] == "ok" and ev[("off", i, s)]["status"][k] == "ok"]
                if ds:
                    per.append(np.mean(ds)); used += 1
            if len(per) < 5:
                res[k] = dict(n_sets=used, decision="too few sets")
                lines.append(f"{name:28s} sets used {used:3d} -> too few sets")
                continue
            m, lo, hi = boot(per, rng)
            res[k] = dict(n_sets=used, mean=m, lo=lo, hi=hi, margin=margin, decision=decide(lo, hi, margin))
            lines.append(f"{name:28s} sets used {used:3d}  off-on mean {m:+.4f} [{lo:+.4f}, {hi:+.4f}]  margin +-{margin:g}  -> {res[k]['decision']}")
        ch = [float(any(ev[("on", i, s)]["pattern"] != ev[("off", i, s)]["pattern"] for s in (1, 2))) for i in members]
        if ch:
            m, lo, hi = boot(ch, rng)
            res["type_change"] = dict(n_sets=len(ch), mean=m, lo=lo, hi=hi, decision=decide_type(lo, hi))
            lines.append(f"{'Pattern type changed':28s} sets {len(ch):3d}  fraction {m:.3f} [{lo:.3f}, {hi:.3f}]  margin 0-0.05 -> {res['type_change']['decision']}")
        base = [float(ev[("on", i, 1)]["pattern"] != ev[("on", i, 2)]["pattern"]) for i in members]
        if base:
            res.setdefault("type_change", {})["seed_baseline"] = float(np.mean(base))
            lines.append(f"{'  reference: seed 1 vs 2 (on)':28s} pattern differs in {np.mean(base):.3f} of sets (not part of the decision)")
        for k, margin, name in METRICS:
            dd = [abs(ev[("on", i, 1)][k] - ev[("on", i, 2)][k]) for i in members
                  if ev[("on", i, 1)]["status"][k] == "ok" and ev[("on", i, 2)]["status"][k] == "ok"]
            if dd:
                lines.append(f"  reference: |seed1 - seed2| (on) {name:24s} median {np.median(dd):.4f}  (n={len(dd)})")
        summary[label] = res
    cats = ["normal", "insufficient", "stalled"]
    tab = np.zeros((3, 3), int)
    for i in complete:
        for s in (1, 2):
            tab[cats.index(run_class(ev[("on", i, s)])), cats.index(run_class(ev[("off", i, s)]))] += 1
    lines.append("\nrun class (rows: field on, columns: field off; normal = not stalled and >= 12 events in 1250-1700):")
    lines.append(f"{'':14s}" + "".join(f"{c:>14s}" for c in cats))
    for r, c in enumerate(cats):
        lines.append(f"{c:14s}" + "".join(f"{v:14d}" for v in tab[r]))
    allok = all(v.get("decision") == "negligible" for v in summary["all"].values())
    lines.append("\nconclusion (all sets): " + ("the field's effect is negligible within the v3 sampling range" if allok else
                 "not all indicators negligible: " + ", ".join(f"{k}={v.get('decision')}" for k, v in summary["all"].items())))
    (OUT / "report.txt").write_text("\n".join(lines) + "\n")
    json.dump(dict(summary=summary, run_class=tab.tolist(), n_sets=len(complete)), open(OUT / "summary.json", "w"), indent=1)
    print("\n".join(lines))
    figure(summary)


def figure(summary):
    plt.rcParams.update({"font.family": "STIXGeneral", "font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.linewidth": 0.6, "savefig.dpi": 400})
    fig, axes = plt.subplots(1, 5, figsize=(13.5 / 2.54, 13.5 / 2.54 * 0.46))
    fig.subplots_adjust(left=0.08, right=0.985, top=0.8, bottom=0.13, wspace=0.8)
    groups = ["all", "R0 holds (transport-limited)", "R0 fails"]
    short = ["All", "Transport-\nlimited", "Not\nlimited"]
    cols = ["k", "#1b7837", "#b2182b"]
    for ax, (k, margin, name) in zip(axes[:4], METRICS):
        ax.axhspan(-margin, margin, color="#e0e0e0", lw=0)
        ax.axhline(0, color="k", lw=0.5)
        for j, g in enumerate(groups):
            r = summary.get(g, {}).get(k, {})
            if "mean" in r:
                ax.errorbar(j, r["mean"], yerr=[[r["mean"] - r["lo"]], [r["hi"] - r["mean"]]], fmt="o", ms=3.5, color=cols[j], capsize=2, lw=0.9)
        ax.set_xticks([]); ax.set_xlim(-0.6, 2.6)
        ax.set_title(name, fontsize=7.5)
    axes[0].set_ylabel("Difference")
    ax = axes[4]
    ax.axhspan(0, TYPE_MARGIN, color="#e0e0e0", lw=0)
    for j, g in enumerate(groups):
        r = summary.get(g, {}).get("type_change", {})
        if "mean" in r:
            ax.errorbar(j, r["mean"], yerr=[[r["mean"] - r["lo"]], [r["hi"] - r["mean"]]], fmt="s", ms=3.5, color=cols[j], capsize=2, lw=0.9)
    for j, g in enumerate(groups):
        b = summary.get(g, {}).get("type_change", {}).get("seed_baseline")
        if b is not None:
            ax.plot([j - 0.3, j + 0.3], [b, b], color="#7f7f7f", lw=1.2, ls=":")
    ax.set_xticks([]); ax.set_xlim(-0.6, 2.6)
    ax.set_title("Type changed", fontsize=7.5); ax.set_ylim(0, 1)
    n = [summary.get(g, {}).get("type_change", {}).get("n_sets", 0) for g in groups]
    hs = [plt.Line2D([], [], ls="", marker="o", color=cols[j], ms=4, label=f"{lab} ({n[j]} sets)")
          for j, lab in enumerate(["All", "Transport-limited", "Not transport-limited"])]
    hs.append(plt.Line2D([], [], color="#7f7f7f", ls=":", lw=1.2, label="Seed 1 vs 2 (reference)"))
    fig.legend(handles=hs, loc="lower center", ncol=4, frameon=False, fontsize=6.5, bbox_to_anchor=(0.5, 0.0))
    fig.text(0.5, 0.98, "Field off − field on.  Grey: pre-specified equivalence range;  bars: 95% interval over parameter sets",
             ha="center", va="top", fontsize=7)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"fig_A1_paired_ablation.{ext}")


if __name__ == "__main__":
    main()
