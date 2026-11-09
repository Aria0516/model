"""Structural change 5 (PROTOCOL.md): the PIN cue and the drain of a primordium come from each cell's own auxin
response m (MONOPTEROS-like; Bhatia et al. 2016), driven by time-integrated auxin (Galvan-Ampudia et al. 2020),
instead of from placed primordium objects. No threshold placement, exclusion radius, follow-then-fix or
secondary field. Initiation events are recorded, never imposed.

  tau_m dm/dt = competent * M^n / (theta^n + M^n) - m,   theta = theta_rel * A_free
  cue_j = A_q m_j ;  epidermis -> inner transfer eta m_j A / (1 + A / K_e) ;  inner vascular drain eta2 m_j
"""
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frozen_v2"))
from layer import TwoLayerSim  # noqa: E402

MP_DEFAULTS = dict(tau_m=3.0, hill_m=4.0, theta_rel_m=0.82, A_free=4.0, m_on=0.5, r_log=2.0)


class MPSim(TwoLayerSim):
    def __init__(self, params, ramp=None):
        self.m = None
        self.logged = []                                  # positions of recorded primordia, moved with the tissue
        p = dict(MP_DEFAULTS)
        p.update(params)
        p.update(Th=1e9, k_I=0.0)                         # no placed primordia, no secondary field
        super().__init__(p, ramp)
        self.m = np.zeros(self.tis.n)
        grow = self.tis.grow                              # TwoLayerSim's wrapper (carries A2)

        def grow_and_carry(g):
            parent = grow(g)
            if self.m is not None:
                self.m = self.m[parent]
            self.logged = [(x * g, y * g) for x, y in self.logged]
            return parent

        self.tis.grow = grow_and_carry

    def _step(self, A):
        p, G = self.p, self.G
        n = G["n"]
        if self.m is None or len(self.m) != n:
            self.m = np.zeros(n)
        G["cue"] = p["A_q"] * self.m                     # PIN points towards responding cells
        G["eta_lin"] = p["eta"] * self.m                 # responding cells drain into the inner layer
        self.vasc = p["eta2"] * self.m
        A_new = super()._step(A)
        ring = (self.rad >= p["R_c"]) & (self.rad < p["R_p"])
        competent = ring | (self.m > p["m_on"])
        M = self.M if (self.M is not None and len(self.M) == n) else A
        th, h = p["theta_rel_m"] * p["A_free"], p["hill_m"]
        Mh = np.maximum(M, 0.0) ** h
        target = competent * Mh / (th ** h + Mh)
        self.m = self.m + p["dt"] * (target - self.m) / p["tau_m"]
        return A_new

    def clusters(self, within=None):
        """Connected groups of responding cells (m > m_on), optionally restricted to a mask."""
        on = self.m > self.p["m_on"]
        if within is not None:
            on = on & within
        idx = np.where(on)[0]
        lab = {i: i for i in idx}

        def find(i):
            while lab[i] != i:
                lab[i] = lab[lab[i]]
                i = lab[i]
            return i
        for a, b in zip(self.tis.src, self.tis.dst):
            if on[a] and on[b]:
                ra, rb = find(a), find(b)
                if ra != rb:
                    lab[ra] = rb
        groups = {}
        for i in idx:
            groups.setdefault(find(i), []).append(i)
        return list(groups.values())

    def _geometry(self, first=False):
        super()._geometry(first)
        if first or self.m is None or len(self.m) != self.tis.n:
            return
        pts = self.tis.pts
        for g in self.clusters():
            w = self.m[g]
            x, y = float((w * pts[g, 0]).sum() / w.sum()), float((w * pts[g, 1]).sum() / w.sum())
            # an initiation is a new patch arising in the competent ring; patches of older primordia that split or
            # flicker after leaving the ring are not new primordia (patch_diag.py, PROTOCOL step 1 addendum)
            if math.hypot(x, y) >= self.p["R_p"]:
                continue
            if all(math.hypot(x - lx, y - ly) > self.p["r_log"] for lx, ly in self.logged):
                self.logged.append((x, y))
                self.log.append((self.t, x, y))
