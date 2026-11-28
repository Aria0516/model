"""First-stage protocol sections 3 and 5 with revision 3 (development group only; groups.json).

python s1_staged.py sites      # section 3: credible sites, developmental time axis (geometry only)
python s1_staged.py signals    # section 5 as changed by revision 5: per-frame staging (Codex labels), t50 and DR5 delay,
                               # GA2020 Fig 4G/H target, bridge to the published measure, sensitivity analyses

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


LABEL_KEY = HERE / "labels" / "out" / "label_key.json"
CODEX = HERE / "labels" / "codex_returned"


def load_sites_codex(seq):
    """Revision 4: positions of the maxima Codex labelled (minima of qDII, ids from all_extrema)."""
    key = {v: k for k, v in json.load(open(LABEL_KEY))["key"].items()}
    code = key[seq]
    lab = pd.read_csv(CODEX / "labels.csv")
    lab = lab[lab.code == code]
    rows = []
    for fr, h in FR.items():
        ex = pd.read_csv(frame_file(seq, fr, "all_extrema"))
        ex = ex[ex.extremum_type == "minimum"].set_index("label")
        rc = float(pd.read_csv(frame_file(seq, fr, "aligned_L1_normalized_signal_data"), usecols=["clv3_radius"]).clv3_radius.iloc[0])
        for _, q in lab[lab.hour == h].iterrows():
            e = ex.loc[int(q.max_id)]
            rows.append(dict(seq=seq, frame=fr, h=h, k=int(q.P), r=float(e.radial_distance), theta=float(e.aligned_theta),
                             x=float(e.aligned_x), y=float(e.aligned_y), rc=rc, confidence=q.confidence))
    return pd.DataFrame(rows)


def codex_direction(seq):
    key = {v: k for k, v in json.load(open(LABEL_KEY))["key"].items()}
    h = pd.read_csv(CODEX / "handedness.csv").set_index("code")
    return h.loc[key[seq], "direction"]


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


def sites_cmd(source="auto"):
    global OUT
    if source == "codex":
        OUT = HERE / "out" / "staged_codex"
    OUT.mkdir(parents=True, exist_ok=True)
    allrows, fits, lines = [], [], []
    for seq in G["development"]:
        marg = handedness_margin(seq)
        s = load_sites(seq) if source == "auto" else load_sites_codex(seq)
        cred, why = credible(s)
        s["credible"] = s.k.map(cred).fillna(False)
        s["reason"] = s.k.map(why)
        s["handedness_margin"] = marg
        allrows.append(s)
        c = s[s.credible]
        fitset = c[(c.k >= 0) & (c.k <= 4)]
        nsite = fitset.groupby("k").size()
        fit = dict(seq=seq, margin=marg, n_credible=int(c.k.nunique()), n_fit_sites=int((nsite >= 2).sum()))
        if source == "auto" and marg < 2:
            fit["status"] = "excluded: handedness margin < 2"
        elif source == "codex" and codex_direction(seq) == "unclear":
            fit["status"] = "excluded: Codex direction unclear"
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
    cred = S[S.credible]
    full = cred.groupby(["seq", "k"]).frame.nunique()
    n_full = sum({0, 1, 2} <= {k for (q, k), n in full.items() if q == seq and n == 3} and
                 F.set_index("seq").status[seq] == "ok" for seq in G["development"])
    lines.append(f"STOP RULE: meristems with credible P0-P2 in all three frames (and included): {n_full}/14 (need >= 8)")
    if source == "codex":
        auto = pd.concat([load_sites(q) for q in G["development"]])
        m = S.merge(auto[["seq", "frame", "k", "r", "theta"]], on=["seq", "frame", "k"], how="outer", suffixes=("_c", "_a"), indicator=True)
        both = m[m._merge == "both"]
        same = ((both.r_c - both.r_a).abs() < 0.5) & ((both.theta_c - both.theta_a + 180) % 360 - 180 < 0.5)
        lines.append(f"agreement with automatic labels (meristem x frame x P): same point {int(same.sum())}, "
                     f"different point {int((~same).sum())}, Codex only {int((m._merge == 'left_only').sum())}, "
                     f"automatic only {int((m._merge == 'right_only').sum())}")
    (OUT / "sites_log.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return n_full


# ---------------------------------------------------------------- section 5, revision 5
OUT5 = HERE / "out" / "staged_signals"
GA = HERE / "ga2020" / "fig4GH_digitized.csv"
QMIN = 0.02
_NUC = {}


def nuclei(seq, fr):
    if (seq, fr) not in _NUC:
        n = pd.read_csv(frame_file(seq, fr, "aligned_L1_normalized_signal_data"),
                        usecols=["aligned_x", "aligned_y", "radial_distance", "clv3_radius", "qDII", "Normalized_DR5", "DR5", "TagBFP", "layer"])
        _NUC[(seq, fr)] = n[n.layer == 1].reset_index(drop=True)
    return _NUC[(seq, fr)]


def kernel_value(n, x, y, col, sigma=3.9):
    """Stand-in for the authors' local 2-D signal at an extremum (tissue_nukem_3d is not installed here).
    A Gaussian of sigma 3.9 um reproduces the authors' extrema table on the development group best among the kernels tried
    (tanh disc 7.5 um / k 0.55: median |diff| 0.002 Auxin; Gaussian 3.9 um: 0.0005 Auxin, 0.0025 x 10^4 DR5); the residual is
    reported in the log. Used only for the bridge with Codex labels."""
    d = np.hypot(n.aligned_x.values - x, n.aligned_y.values - y)
    w = np.exp(-d ** 2 / (2 * sigma ** 2))
    return float((w * n[col].values).sum() / w.sum())


def measures(sub):
    q = sub.qDII.values
    ok = q >= QMIN
    return dict(n=len(q), n_excl=int((~ok).sum()), saturated=bool((~ok).sum() > len(q) / 2),
                lnq=float(np.median(-np.log(q[ok]))) if ok.any() else np.nan,
                aux=float(np.median(1 - q)), ndr5=float(np.median(sub.Normalized_DR5)),
                lr=float(np.median(np.log(sub.DR5.values / sub.TagBFP.values))), dr5raw=float(np.median(sub.DR5)) / 1e4)


def site_values(sites, radius):
    rows = []
    for (seq, fr), g in sites.groupby(["seq", "frame"]):
        n = nuclei(seq, fr)
        X = n[["aligned_x", "aligned_y"]].values
        D = np.hypot(X[:, None, 0] - g.x.values[None], X[:, None, 1] - g.y.values[None])
        rc = float(n.clv3_radius.iloc[0])
        ref = measures(n[(n.radial_distance >= rc) & (n.radial_distance <= 55) & (D.min(1) > 9)])
        for j, (_, s) in enumerate(g.iterrows()):
            near = n[D[:, j] <= radius]
            r = dict(s)
            if len(near) < 4:
                r.update(n=len(near))
                rows.append(r); continue
            m = measures(near)
            if m["saturated"]:
                m["lnq"] = np.nan
            r.update(m)
            for key in ("lnq", "aux", "ndr5", "lr"):
                r[f"c_{key}"] = m[key] - ref[key]
            r["ext_aux"] = 1 - kernel_value(n, s.x, s.y, "qDII")
            r["ext_dr5"] = kernel_value(n, s.x, s.y, "DR5") / 1e4
            rows.append(r)
    return pd.DataFrame(rows)


def cells(df, col, T=12.0, mins=5, minm=3):
    d = df.dropna(subset=[col])
    c = d.groupby(["k", "h"]).agg(med=(col, "median"), n=(col, "size"), nm=("seq", "nunique")).reset_index()
    c = c[(c.n >= mins) & (c.nm >= minm)].copy()
    c["tau"] = T * c.k + c.h
    return c.sort_values("tau").reset_index(drop=True)


def t50(c):
    """Baseline = median of cells with tau < -18 h; plateau = max cell; first upward crossing of the midpoint."""
    if c is None or len(c) < 2:
        return dict(t50=np.nan, why="too few cells")
    base = c[c.tau < -18].med
    if not len(base):
        return dict(t50=np.nan, why="no baseline cell")
    b, p = float(base.median()), float(c.med.max())
    mid = (b + p) / 2
    t, v = c.tau.values, c.med.values
    for i in range(len(v) - 1):
        if v[i] < mid <= v[i + 1]:
            return dict(t50=float(t[i] + (mid - v[i]) / (v[i + 1] - v[i]) * (t[i + 1] - t[i])), base=b, plateau=p, mid=mid,
                        peak_tau=float(t[np.argmax(v)]), why="ok")
    return dict(t50=np.nan, base=b, plateau=p, why="no crossing")


def delay(df, cin, cout, T=12.0):
    a, b = t50(cells(df, cin, T)), t50(cells(df, cout, T))
    return b["t50"] - a["t50"], a, b


def boot_delay(df, cin, cout, T=12.0, nboot=1000, seed=20261128):
    rng = np.random.default_rng(seed)
    seqs = df.seq.unique()
    groups = {q: g for q, g in df.groupby("seq")}
    vals = []
    for i in range(nboot):
        pick = rng.choice(seqs, len(seqs), replace=True)
        bd = pd.concat([groups[q].assign(seq=f"{q}#{j}") for j, q in enumerate(pick)])
        vals.append(delay(bd, cin, cout, T)[0])
    v = np.array(vals)
    good = v[np.isfinite(v)]
    return dict(median=float(np.median(good)) if len(good) else np.nan,
                lo=float(np.percentile(good, 2.5)) if len(good) else np.nan,
                hi=float(np.percentile(good, 97.5)) if len(good) else np.nan,
                fail=float(1 - len(good) / nboot))


def published():
    d = pd.read_csv(GA)
    out = {}
    for scale in ("auxin", "lnq"):
        a = d[d.panel == "G"].rename(columns={"stage": "k", "hour": "h"}).copy()
        if scale == "lnq":
            a["median"] = -np.log(1 - a["median"])
        ca = a.assign(med=a["median"], tau=12 * a.k + a.h).sort_values("tau").reset_index(drop=True)
        b = d[d.panel == "H"].rename(columns={"stage": "k", "hour": "h"})
        cb = b.assign(med=b["median"], tau=12 * b.k + b.h).sort_values("tau").reset_index(drop=True)
        ta, tb = t50(ca), t50(cb)
        out[scale] = dict(t50_in=ta, t50_dr5=tb, delay=tb["t50"] - ta["t50"])
    return out


def signals_cmd():
    OUT5.mkdir(parents=True, exist_ok=True)
    lines = []
    S = pd.concat([load_sites_codex(q) for q in G["development"]], ignore_index=True)
    cred = pd.read_csv(HERE / "out" / "staged_codex" / "sites.csv")[["seq", "frame", "k", "credible"]]
    S = S.merge(cred, on=["seq", "frame", "k"], how="left")
    V7, V10 = site_values(S, 7.0), site_values(S, 10.0)
    V7.to_csv(OUT5 / "site_values_r7.csv", index=False)
    V10.to_csv(OUT5 / "site_values_r10.csv", index=False)
    lines.append(f"development group: {S.seq.nunique()} meristems, {len(S)} labelled site-frames (Codex, all confidence levels)")
    few = V7[V7.n < 4]
    lines.append(f"sites with < 4 nuclei within 7 um: {len(few)} (by P: {few.k.value_counts().sort_index().to_dict()}; median r {few.r.median():.1f} um, "
                 f"outside the L1 nuclei crop); saturated (-ln qDII not used): {int(V7.saturated.fillna(False).sum())}")

    # bridge 0: our kernel reimplementation vs the authors' extrema table at the same points
    chk = []
    for seq in G["development"]:
        for fr, h in FR.items():
            pe = pd.read_csv(frame_file(seq, fr, "aligned_primordia_extrema"))
            pe = pe[pe.extremum_type == "minimum"]
            n = nuclei(seq, fr)
            for _, e in pe.iterrows():
                chk.append(dict(seq=seq, frame=fr, h=h, k=int(e.primordium), Auxin=e.Auxin, DR5=e.DR5 / 1e4,
                                my_aux=1 - kernel_value(n, e.aligned_x, e.aligned_y, "qDII"),
                                my_dr5=kernel_value(n, e.aligned_x, e.aligned_y, "DR5") / 1e4))
    A = pd.DataFrame(chk)
    A.to_csv(OUT5 / "authors_extrema_dev.csv", index=False)
    lines.append(f"kernel stand-in vs authors' extrema table ({len(A)} points): |diff| median / max  Auxin "
                 f"{np.abs(A.Auxin - A.my_aux).median():.4f} / {np.abs(A.Auxin - A.my_aux).max():.4f}, "
                 f"DR5 {np.abs(A.DR5 - A.my_dr5).median():.4f} / {np.abs(A.DR5 - A.my_dr5).max():.4f} (10^4)")

    # target: published curves
    P = published()
    res = dict(published=P)
    for sc in ("auxin", "lnq"):
        p = P[sc]
        lines.append(f"PUBLISHED (GA2020 Fig 4G/H, N=21, {sc} scale): t50 input {p['t50_in']['t50']:+.1f} h, "
                     f"t50 DR5 {p['t50_dr5']['t50']:+.1f} h, delay {p['delay']:+.1f} h; DR5 peak at tau {p['t50_dr5']['peak_tau']:+.0f} h")

    # bridge 1 and 2: published measure on the development group
    ga = pd.read_csv(GA)
    gm = {(r.panel, r.stage, r.hour): r["median"] for _, r in ga.iterrows()}
    bridge = {}
    for name, D, ca, cd in (("authors' labels", A, "Auxin", "DR5"), ("Codex labels", V7, "ext_aux", "ext_dr5")):
        Ca, Cd = cells(D, ca, mins=1, minm=1), cells(D, cd, mins=1, minm=1)
        ma = np.mean([abs(r.med - gm[("G", r.k, r.h)]) for _, r in Ca.iterrows() if ("G", r.k, r.h) in gm])
        md = np.mean([abs(r.med - gm[("H", r.k, r.h)]) for _, r in Cd.iterrows() if ("H", r.k, r.h) in gm])
        dl, ta, tb = delay(D, ca, cd)
        bridge[name] = dict(mad_auxin=float(ma), mad_dr5=float(md), delay=float(dl), t50_in=ta, t50_dr5=tb,
                            cells_auxin=Ca[["k", "h", "med", "n", "nm"]].to_dict("records"), cells_dr5=Cd[["k", "h", "med", "n", "nm"]].to_dict("records"))
        rat = [r.med / gm[("H", r.k, r.h)] for _, r in Cd.iterrows() if ("H", r.k, r.h) in gm]
        bridge[name]["dr5_ratio_median"] = float(np.median(rat))
        lines.append(f"BRIDGE {name}: dev / published DR5 median ratio over cells {np.median(rat):.2f} (range {min(rat):.2f}-{max(rat):.2f})")
        lines.append(f"BRIDGE {name}: mean |dev median - published median| over P-3..P1 cells: Auxin {ma:.3f}, DR5 {md:.3f} (10^4); "
                     f"delay {dl:+.1f} h (t50 input {ta['t50']:+.1f}, DR5 {tb['t50']:+.1f})")
    res["bridge"] = bridge

    # main exploratory analysis and sensitivity analyses
    nolow = V7[V7.confidence != "low"]
    analyses = [
        ("main: -ln qDII, Normalized DR5, contrast, r 7 um, T 12 h", V7, "c_lnq", "c_ndr5", 12.0),
        ("T = 11.9 h", V7, "c_lnq", "c_ndr5", 11.9),
        ("T = 9.2 h", V7, "c_lnq", "c_ndr5", 9.2),
        ("T = 16.4 h", V7, "c_lnq", "c_ndr5", 16.4),
        ("without low-confidence labels", nolow, "c_lnq", "c_ndr5", 12.0),
        ("radius 10 um", V10, "c_lnq", "c_ndr5", 12.0),
        ("input 1 - qDII", V7, "c_aux", "c_ndr5", 12.0),
        ("output ln(DR5/TagBFP)", V7, "c_lnq", "c_lr", 12.0),
        ("no reference subtraction", V7, "lnq", "ndr5", 12.0),
        ("without DR5-TEST", V7[~V7.seq.str.contains("DR5-TEST")], "c_lnq", "c_ndr5", 12.0),
        ("cross-frame credible sites only", V7[V7.credible.fillna(False).astype(bool)], "c_lnq", "c_ndr5", 12.0),
    ]
    res["analyses"] = []
    for name, D, ci, co, T in analyses:
        dl, ta, tb = delay(D, ci, co, T)
        bt = boot_delay(D, ci, co, T)
        res["analyses"].append(dict(name=name, n_meristems=int(D.seq.nunique()), n_sites=int(D[[ci, co]].dropna().shape[0]),
                                    delay=float(dl), t50_in=ta, t50_dr5=tb, boot=bt, T=T, cin=ci, cout=co))
        lines.append(f"{name:55s} t50 input {ta['t50']:+6.1f} h  DR5 {tb['t50']:+6.1f} h  delay {dl:+6.1f} h  "
                     f"95% [{bt['lo']:+.1f}, {bt['hi']:+.1f}]  boot failures {bt['fail']:.1%}  (DR5 peak tau {tb.get('peak_tau', np.nan):+.0f} h)")
    main = cells(V7, "c_lnq"), cells(V7, "c_ndr5")
    main[0].to_csv(OUT5 / "cells_main_input.csv", index=False)
    main[1].to_csv(OUT5 / "cells_main_dr5.csv", index=False)

    # same organ 0 h -> 10 h
    pair = V7.pivot_table(index=["seq", "k"], columns="h", values=["c_lnq", "c_ndr5"])
    pr = []
    for k in sorted(V7.k.unique()):
        for col, cc in (("c_lnq", main[0]), ("c_ndr5", main[1])):
            try:
                dd = (pair[(col, 10)] - pair[(col, 0)]).xs(k, level="k").dropna()
            except KeyError:
                continue
            c0, c1 = cc[(cc.k == k) & (cc.h == 0)].med, cc[(cc.k == k) & (cc.h == 10)].med
            pr.append(dict(k=int(k), measure=col, n_pairs=len(dd), paired_median=float(dd.median()) if len(dd) else np.nan,
                           cell_diff=float(c1.iloc[0] - c0.iloc[0]) if len(c0) and len(c1) else np.nan))
    res["same_organ_0_10h"] = pr
    lines.append("same organ 10 h - 0 h (paired median | cell difference):")
    for r in pr:
        lines.append(f"   P{r['k']:+d} {r['measure']:7s} n {r['n_pairs']:2d}  {r['paired_median']:+.3f} | {r['cell_diff']:+.3f}")
    lines.append("STOP RULE (section 10) was triggered in section 3; everything above except the published target is exploratory.")
    json.dump(res, open(OUT5 / "summary.json", "w"), indent=1, default=float)
    (OUT5 / "signals_log.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    if sys.argv[1] == "sites":
        sites_cmd(sys.argv[2] if len(sys.argv) > 2 else "auto")
    elif sys.argv[1] == "signals":
        signals_cmd()
