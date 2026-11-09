"""Noise statistics that can be compared with Galvan-Ampudia et al. 2020.

The paper reports the angular spread of primordia P1..P5 after aligning meristems on P0
(6.7 deg). The matching model statistic is the spread of theta[n-k] - theta[n] for k = 1..5,
not the spread of successive divergence angles alone.
"""
import math
import numpy as np

import analysis


def rank_spread(log, kmax=6, skip=1 / 3):
    """Circular sd of the angle between a primordium and the k-th older one, k = 1..kmax."""
    t, th, rb = analysis.sequence(log, skip)
    out = []
    for k in range(1, kmax + 1):
        if len(th) <= k + 5:
            out.append(float("nan")); continue
        _, sd = analysis.circ_stats((th[k:] - th[:-k]) % 360)
        out.append(sd)
    return out


def divergence_autocorr(log, skip=1 / 3):
    """Lag-1 autocorrelation of divergence deviations.

    -0.5 means independent placement errors on a fixed lattice (errors do not accumulate);
    0 means errors accumulate like a random walk, the assumption behind the paper's 3.6 deg.
    """
    t, th, rb = analysis.sequence(log, skip)
    d = np.diff(th) % 360
    mean, _ = analysis.circ_stats(d)
    e = (d - mean + 180) % 360 - 180
    if len(e) < 8:
        return float("nan")
    return float(np.corrcoef(e[:-1], e[1:])[0, 1])


def node_rank_spread(log, jug, kmax=3, skip=1 / 3):
    """Same idea for whorled patterns: spread of the rotation between whorl n and whorl n-k."""
    t, th, rb = analysis.sequence(log, skip)
    grp, _ = analysis.nodes(t, th)
    per = 360.0 / jug
    ph = []
    for g in grp:
        if len(g) == jug:
            z = np.exp(1j * np.radians(jug * th[g])).mean()
            ph.append((math.degrees(math.atan2(z.imag, z.real)) % 360) / jug)
    ph = np.array(ph)
    out = []
    for k in range(1, kmax + 1):
        if len(ph) <= k + 4:
            out.append(float("nan")); continue
        _, sd = analysis.circ_stats(((ph[k:] - ph[:-k]) % per) * jug)
        out.append(sd / jug)
    return out
