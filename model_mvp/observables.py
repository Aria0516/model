"""Observation definitions shared by model runs and data (implementation plan step 1; definitions in OBSERVABLES.md).

All statistics are computed from an initiation log [(t, x, y), ...] in model units, restricted to the analysis window.
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "detuned_v3" / "frozen_v3"))
import analysis  # noqa: E402
import noise_tools  # noqa: E402

T0, T1 = 1250.0, 1700.0
HOURS_PER_UNIT = 1.6                         # v3 time unit; to be replaced by the measured growth rate (plan step 3, B6)
UM_PER_UNIT = 4.907545364810229              # calib_v2
WINDOW_H = 12.0                              # Besnard 2014 imaged every 12 h
N_OFFSETS = 6                                # window start positions spread evenly over one window
MIN_EVENTS = dict(alpha=7, nc=7, gap_cv=7, hours=7, G=7, r_um=7, spread=12, coinit_org=6, coinit_win=6, pattern=12)


def coinitiation(t, t0=T0, t1=T1, hours_per_unit=HOURS_PER_UNIT):
    """Resample initiation times into 12 h windows; average over window start positions.

    coinit_org: fraction of primordia that share their window with at least one other primordium.
    coinit_win: fraction of windows with >= 1 primordium that hold >= 2.
    Only complete windows inside [t0, t1) are used."""
    W = WINDOW_H / hours_per_unit
    org, win, nwin = [], [], []
    for k in range(N_OFFSETS):
        start = t0 + k * W / N_OFFSETS
        nfull = int((t1 - start) // W)
        if nfull < 1:
            continue
        tt = np.asarray([x for x in t if start <= x < start + nfull * W])
        if len(tt) == 0:
            continue
        b = np.bincount(((tt - start) // W).astype(int), minlength=nfull)
        occ = b[b > 0]
        org.append(float(occ[occ >= 2].sum() / occ.sum()))
        win.append(float((occ >= 2).mean()))
        nwin.append(nfull)
    return (float(np.mean(org)) if org else float("nan"), float(np.mean(win)) if win else float("nan"),
            int(min(nwin)) if nwin else 0)


def evaluate(log, gamma=0.03, t0=T0, t1=T1, hours_per_unit=HOURS_PER_UNIT):
    late = sorted([tuple(l[:3]) for l in log if t0 <= l[0] < t1])
    n = len(late)
    stalled = not any(l[0] >= 0.5 * (t0 + t1) for l in late)
    out = dict(n=n, stalled=stalled, status={})
    for k, m in MIN_EVENTS.items():
        out["status"][k] = "stalled" if stalled else ("ok" if n >= m else "insufficient")
    ok = lambda k: out["status"][k] == "ok"
    if n >= 2:
        t, th, rb = analysis.sequence(late, skip=0.0)
        gaps = np.diff(t)
    if ok("alpha"):
        a, f1, fp, fo, sd1 = analysis.lattice_fit(np.diff(th))
        out["alpha"], out["nc"] = float(min(a, 360 - a)), float(1 - f1)
    if ok("gap_cv"):
        out["gap_cv"] = float(gaps.std() / gaps.mean())
        out["hours"] = float(gaps.mean() * hours_per_unit)
        out["G"] = float(gamma * gaps.mean())
        out["r_um"] = float(np.median([math.hypot(l[1], l[2]) * UM_PER_UNIT for l in late]))
    if ok("spread"):
        out["spread"] = float(np.nanmean(noise_tools.rank_spread(late, kmax=5, skip=0.0)))
    if ok("coinit_org"):
        o, w, nw = coinitiation([l[0] for l in late], t0, t1, hours_per_unit)
        out["coinit_org"], out["coinit_win"], out["n_windows"] = o, w, nw
        if nw < 4:
            out["status"]["coinit_org"] = out["status"]["coinit_win"] = "insufficient"
            out.pop("coinit_org"); out.pop("coinit_win")
    out["pattern"] = analysis.summarize(late, gamma, skip=0.0)["pattern"] if ok("pattern") else ("stalled" if stalled else "too_few")
    return out
