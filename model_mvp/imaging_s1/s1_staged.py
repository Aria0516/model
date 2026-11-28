"""First-stage protocol sections 3 and 5 with revision 3 (development group only; groups.json).

python s1_staged.py sites      # section 3: credible sites, developmental time axis (geometry only)
python s1_staged.py signals    # section 5: staged input / DR5 contrasts, t50 and DR5 delay

Implementation details fixed before running (not stated in the protocol text):
- cross-frame check between consecutive frames in which a site is present; for a 10 h gap the radius-ratio range is
  squared (0.81-1.82) and the azimuth limit stays 15 deg;
- the within-frame order check is applied per frame; a violation in any frame makes both sites not credible;
- the time-axis fit uses credible sites with k = 0..4; the resulting tau is applied to all credible sites (k = -3..5);
- 6 h bins are [6j, 6j + 6) h; a curve's baseline uses bins whose upper edge is <= -18 h.
"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "staged"
G = json.load(open(HERE / "groups.json"))
DATA = HERE.parents[1] / "reproductions" / "elife55832" / "outputs" / "nuclei_21"
FR = {"t00": 0, "t05": 5, "t10": 10}
T_PLAST = 12.0
RNG = np.random.default_rng(20261128)


def frame_file(seq, fr, kind):
    return next((DATA / seq).rglob(f"*_{fr}_{kind}.csv"))


def handedness_margin(seq):
    line = (DATA / seq / "handedness.txt").read_text().splitlines()[0]
    m = re.search(r"score now ([+-]?\d+\.\d+)", line) or re.search(r"score ([+-]?\d+\.\d+)", line)
    return abs(float(m.group(1)))


# ---------------------------------------------------------------- section 3
def load_sites(seq):
    rows = []
    for fr, h in FR.items():
        e = pd.read_csv(frame_file(seq, fr, "aligned_primordia_extrema"))
        e = e[e.extremum_type == "minimum"]
        rc = float(e.clv3_radius.iloc[0]) if len(e) else np.nan
        for _, q in e.iterrows():
            rows.append(dict(seq=seq, frame=fr, h=h, k=int(q.primordium), r=float(q.radial_distance), theta=float(q.aligned_theta),
                             x=float(q.aligned_x), y=float(q.aligned_y), rc=rc))
    return pd.DataFrame(rows)


def credible(sites):
    out, reason = {}, {}
    for k, g in sites.groupby("k"):
        g = g.sort_values("h")
        if len(g) < 2:
            out[k] = False; reason[k] = "one frame only"; continue
        ok = True
        for (_, a), (_, b) in zip(g.iloc[:-1].iterrows(), g.iloc[1:].iterrows()):
            n = (b.h - a.h) / 5
            dth = abs((b.theta - a.theta + 180) % 360 - 180)
            ratio = b.r / a.r
            if dth > 15 or not (0.9 ** n <= ratio <= 1.35 ** n):
                ok = False; reason[k] = f"jump {a.frame}->{b.frame}: dtheta {dth:.0f} deg, r ratio {ratio:.2f}"; break
        out[k] = ok
        if ok:
            reason[k] = "ok"
    for fr in FR:                                           # within-frame order
        f = sites[(sites.frame == fr) & sites.k.map(lambda k: out.get(k, False))].sort_values("k")
        ks, rs = f.k.values, f.r.values
        for i in range(len(ks) - 1):
            if rs[i + 1] <= rs[i]:
                for kk in (ks[i], ks[i + 1]):
                    out[kk] = False; reason[kk] = f"order violated at {fr} (P{ks[i]} r {rs[i]:.1f} >= P{ks[i+1]} r {rs[i+1]:.1f})"
    return out, reason


def window_edge_fraction(s):
    """Share of credible observations within 10% of the authors' radius window (in CLV3-radius units)."""
    rmin = 0.8 + 0.2 * s.k; rmax = 1.7 + 0.25 * s.k
    x = s.r / s.rc
    return float(((abs(x - rmin) / rmin <= 0.1) | (abs(x - rmax) / rmax <= 0.1)).mean())


def sites_cmd():
    OUT.mkdir(parents=True, exist_ok=True)
    allrows, fits, lines = [], [], []
    for seq in G["development"]:
        marg = handedness_margin(seq)
        s = load_sites(seq)
        cred, why = credible(s)
        s["credible"] = s.k.map(cred).fillna(False)
        s["reason"] = s.k.map(why)
        s["handedness_margin"] = marg
        allrows.append(s)
        c = s[s.credible]
        fitset = c[(c.k >= 0) & (c.k <= 4)]
        nsite = fitset.groupby("k").size()
        fit = dict(seq=seq, margin=marg, n_credible=int(c.k.nunique()), n_fit_sites=int((nsite >= 2).sum()))
        if marg < 2:
            fit["status"] = "excluded: handedness margin < 2"
        elif (nsite >= 2).sum() < 3:
            fit["status"] = "excluded: fewer than 3 credible sites (k = 0..4) with >= 2 frames"
        else:
            A = np.c_[np.ones(len(fitset)), fitset.k, fitset.h]
            a, Gs, v = np.linalg.lstsq(A, np.log(fitset.r), rcond=None)[0]
            fit.update(status="ok", a=float(a), G=float(Gs), v=float(v), T_hat=float(Gs / v) if v > 0 else float("nan"),
                       edge_frac=window_edge_fraction(c))
        fits.append(fit)
    S = pd.concat(allrows)
    F = pd.DataFrame(fits)
    ok = F[F.status == "ok"]
    a_med = float(ok.a.median())
    F["delta"] = np.where(F.status == "ok", (F.a - a_med) / F.G, np.nan)
    S = S.merge(F[["seq", "delta", "status"]], on="seq", how="left")
    S["stage"] = S.k + S.delta
    S["tau"] = S.stage * T_PLAST + S.h
    S["tau_nophase"] = S.k * T_PLAST + S.h
    S.to_csv(OUT / "sites.csv", index=False)
    F.to_csv(OUT / "time_axis.csv", index=False)
    lines.append(f"development group: {len(F)} meristems; time axis fitted for {len(ok)}")
    for _, f in F.iterrows():
        extra = (f"  a {f.a:.3f}  G_s {f.G:.3f}  v_s {f.v:.4f}/h  T_hat {f.T_hat:.1f} h  phase {f.delta:+.2f}  edge-of-window {f.edge_frac:.2f}"
                 if f.status == "ok" else "")
        lines.append(f"{f.seq[-22:]:22s} handedness {f.margin:5.2f}  credible sites {f.n_credible}  fit sites {f.n_fit_sites}  {f.status}{extra}")
    lines.append(f"T_hat over fitted meristems: median {ok.T_hat.median():.1f} h, quartiles {ok.T_hat.quantile(.25):.1f}-{ok.T_hat.quantile(.75):.1f} h")
    used = S[S.status == "ok"]
    lines.append(f"sites in fitted meristems: {used.groupby(['seq', 'k']).ngroups} labelled, {used[used.credible].groupby(['seq', 'k']).ngroups} credible")
    lines.append("reasons for non-credible sites (fitted meristems): " + json.dumps(
        used[~used.credible].drop_duplicates(["seq", "k"]).reason.str.split(":").str[0].value_counts().to_dict()))
    (OUT / "sites_log.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    {"sites": sites_cmd}[sys.argv[1]]()
