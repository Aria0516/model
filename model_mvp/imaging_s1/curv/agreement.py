"""Agreement between the frozen automatic criterion and Codex (PROTOCOL revision 2). Development group only.

Matching: within each meristem, one-to-one greedy pairing of sites whose first-visible centres are <= 10 um apart.
Region: a pair counts if the mean of its two centres lies 22-48 um from the apex; an unmatched site counts if its own
centre does. Categories: visible_0h, event_0_5, event_5_10, unclear, absent (not marked by that method).
Judgeable = event_0_5 or event_5_10.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
KEY = json.load(open(HERE / "out" / "blind_key.json"))["key"]
G = json.load(open(HERE.parent / "groups.json"))
import sys
R_IN, R_OUT = 22.0, 48.0
MATCH = float(sys.argv[1]) if len(sys.argv) > 1 else 10.0          # 10 um is the pre-specified value; others are sensitivity only
rng = np.random.default_rng(0)


def auto_cat(row):
    if row.label == "visible_at_0h":
        return "visible_0h"
    if row.label == "event":
        return "event_0_5" if row.interval == "(0,5]" else "event_5_10"
    return "unclear"


def codex_cat(v):
    return {"0": "visible_0h", "5": "event_0_5", "10": "event_5_10", "unclear": "unclear"}.get(str(v), "none")


auto = pd.read_csv(HERE / "out" / "auto_sites_development.csv")
auto["cat"] = auto.apply(auto_cat, axis=1)
cx = pd.read_csv(HERE / "codex_returned" / "labels.csv", dtype={"first_visible": str})
cx["meristem"] = cx.code.map(KEY)
cx = cx[cx.first_visible != "none"].copy()
cx["cat"] = cx.first_visible.map(codex_cat)

rows = []
for m in G["development"]:
    a = auto[auto.meristem == m].reset_index(drop=True)
    c = cx[cx.meristem == m].reset_index(drop=True)
    pairs = sorted(((np.hypot(a.x[i] - c.x_um[j], a.y[i] - c.y_um[j]), i, j) for i in range(len(a)) for j in range(len(c))))
    ua, uc = set(), set()
    for dist, i, j in pairs:
        if dist <= MATCH and i not in ua and j not in uc:
            ua.add(i); uc.add(j)
            xm, ym = (a.x[i] + c.x_um[j]) / 2, (a.y[i] + c.y_um[j]) / 2
            rows.append(dict(meristem=m, x=xm, y=ym, auto=a.cat[i], codex=c.cat[j], codex_conf=c.confidence[j], dist=dist))
    for i in set(range(len(a))) - ua:
        rows.append(dict(meristem=m, x=a.x[i], y=a.y[i], auto=a.cat[i], codex="absent", codex_conf="", dist=np.nan))
    for j in set(range(len(c))) - uc:
        rows.append(dict(meristem=m, x=c.x_um[j], y=c.y_um[j], auto="absent", codex=c.cat[j], codex_conf=c.confidence[j], dist=np.nan))
S = pd.DataFrame(rows)
S["r"] = np.hypot(S.x, S.y)
S["in_region"] = (S.r >= R_IN) & (S.r <= R_OUT)
S.to_csv(HERE / "out" / ("agreement_sites.csv" if MATCH == 10.0 else f"agreement_sites_match{MATCH:g}.csv"), index=False)
R = S[S.in_region].copy()

print("all sites (before region):", len(S), "| in region 22-48 um:", len(R))
print("\ncross table in region (rows: automatic, columns: Codex):")
order = ["visible_0h", "event_0_5", "event_5_10", "unclear", "absent"]
print(pd.crosstab(R.auto, R.codex).reindex(index=order, columns=order, fill_value=0).to_string())

J = lambda s: s.isin(["event_0_5", "event_5_10"])
ja, jc = J(R.auto).values, J(R.codex).values


def kappa(x, y):
    po = np.mean(x == y)
    pe = x.mean() * y.mean() + (1 - x.mean()) * (1 - y.mean())
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


k = kappa(ja, jc)
idx = np.arange(len(R)); mer = R.meristem.values
ks = []
for _ in range(2000):                                   # bootstrap over meristems
    pick = rng.choice(G["development"], len(G["development"]))
    sel = np.concatenate([idx[mer == p] for p in pick])
    ks.append(kappa(ja[sel], jc[sel]))
both = ja & jc
interval_same = (R.auto.values[both] == R.codex.values[both])
print(f"\njudgeable: automatic {ja.sum()}, Codex {jc.sum()}, both {both.sum()}")
print(f"Cohen kappa (judgeable vs not) = {k:.2f}  [95% bootstrap over meristems {np.nanpercentile(ks, 2.5):.2f}, {np.nanpercentile(ks, 97.5):.2f}]  (standard >= 0.6)")
print(f"interval agreement among both-judgeable: {interval_same.sum()}/{both.sum()}" + (f" = {interval_same.mean():.2f}" if both.sum() else "") + "  (standard >= 0.80)")


def counts(mask, label):
    per = R[mask].groupby("meristem").size().reindex(G["development"], fill_value=0)
    print(f"{label:28s} meristems with >=1 event {int((per > 0).sum())}/14 (>= 8) | events {int(per.sum())} (>= 20) | largest share "
          f"{(per.max() / per.sum()) if per.sum() else float('nan'):.2f} (<= 0.25)")


print()
counts(ja, "automatic only")
counts(jc, "Codex only")
counts(both, "both judgeable (consensus)")
print("\nCodex: first_visible in region:", R.codex.value_counts().to_dict())
print("automatic: categories in region:", R.auto.value_counts().to_dict())
