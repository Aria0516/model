"""Automatic bulge detector for the blind morphology check (step 1). Uses ONLY nuclear coordinates (0 h frame) and curvature.

Height residual: per frame, fit z = a + b x + c y + d r^2 + e r^4 to L1 nuclei within R_FIT of the 0 h apex;
residual = z - fit, median-smoothed over SMOOTH um. A bulge = a connected group (links <= LINK um) of >= MIN_N nuclei with
smoothed residual >= THR um and positive smoothed mean curvature, centroid in R_IN..R_OUT um from the apex.
Tracks: bulges in consecutive frames whose centroids are within TRACK um are the same site.
"""
import numpy as np
from scipy.sparse.csgraph import connected_components
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree

from curvlib import FRAMES, apex, smooth

R_FIT, SMOOTH, LINK, MIN_N, THR = 45.0, 5.0, 7.0, 5, 1.0
R_IN, R_OUT, TRACK, COVER = 22.0, 48.0, 10.0, 5.0
HOURS = {"t00": 0, "t05": 5, "t10": 10}


def residual(d, c):
    x, y = d.x.values - c[0], d.y.values - c[1]
    r2 = x ** 2 + y ** 2
    m = r2 < R_FIT ** 2
    A = np.c_[np.ones(len(x)), x, y, r2, r2 ** 2]
    beta = np.linalg.lstsq(A[m], d.z.values[m], rcond=None)[0]
    return x, y, d.z.values - A @ beta


def bulges(d, c):
    x, y, res = residual(d, c)
    dd = d.assign(x=x, y=y, res=res)
    rs, hs = smooth(dd, "res", SMOOTH), smooth(dd, "H", SMOOTH)
    keep = np.where((rs >= THR) & (hs > 0))[0]
    if len(keep) == 0:
        return [], dd
    pts = np.c_[x[keep], y[keep]]
    pairs = cKDTree(pts).query_pairs(LINK, output_type="ndarray")
    n = len(keep)
    g = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n)) if len(pairs) else coo_matrix((n, n))
    _, lab = connected_components(g, directed=False)
    out = []
    for k in np.unique(lab):
        idx = keep[lab == k]
        if len(idx) < MIN_N:
            continue
        cx, cy = x[idx].mean(), y[idx].mean()
        r = np.hypot(cx, cy)
        if R_IN <= r <= R_OUT:
            out.append(dict(x=float(cx), y=float(cy), r=float(r), n=int(len(idx)), peak=float(rs[idx].max())))
    return out, dd


def covered(dd, x, y):
    return bool(np.hypot(dd.x.values - x, dd.y.values - y).min() <= COVER) and np.hypot(x, y) <= R_OUT


def classify(seq):
    """Return the list of sites with first-visible frame and a judgeability label."""
    c = apex(seq["t00"])
    det = {fr: bulges(seq[fr], c) for fr in FRAMES}
    tracks = []
    for fr in FRAMES:
        for b in det[fr][0]:
            for t in tracks:
                last_fr, last = t["obs"][-1]
                if FRAMES.index(last_fr) == FRAMES.index(fr) - 1 and np.hypot(last["x"] - b["x"], last["y"] - b["y"]) <= TRACK and not t.get("_used_" + fr):
                    t["obs"].append((fr, b)); t["_used_" + fr] = True
                    break
            else:
                tracks.append(dict(obs=[(fr, b)]))
    sites = []
    for t in tracks:
        frs = [f for f, _ in t["obs"]]
        first, b = t["obs"][0]
        contiguous_to_end = frs == list(FRAMES[FRAMES.index(first):])
        if first == "t00":
            label, interval = "visible_at_0h", None
        elif not contiguous_to_end:
            label, interval = "unclear_disappears", None
        else:
            prev = FRAMES[FRAMES.index(first) - 1]
            ok = covered(det[prev][1], b["x"], b["y"])
            label = "event" if ok else "unclear_not_covered"
            interval = (HOURS[prev], HOURS[first]) if ok else None
        sites.append(dict(first_visible=first, frames=frs, x=b["x"], y=b["y"], r=b["r"], n=b["n"], label=label, interval=interval))
    return sites, c, det
