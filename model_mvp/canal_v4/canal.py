"""Structural change 4 (candidate 1): primordia as drains that build themselves up from the flux they carry
(canalization, Mitchison 1980; with-the-flux polarization in inner tissue, Bayer et al. 2009; midvein drainage,
Deb et al. 2015). Replaces the four object rules of the main line (threshold placement, exclusion radius,
follow-then-fix, secondary field) with one cell-level variable.

Each cell has a drain capacity c (c0 .. eta). Auxin moves from the epidermis into the inner layer through
  c * A / (1 + A / K_e)            (the old primordium sink, now carried by cells instead of placed objects)
  + k_v * (A - A2)                 (passive exchange, as in the main line; it does not feed the drain back)
The capacity is reinforced by the flux that the drain itself carries, J = c A / (1 + A / K_e):
  dc/dt = (c0 + eta * J^n / (J_K^n + J^n) * competent - c) / tau_can
c0 = c0_frac * eta is a small basal capacity in every cell (the seed). For n = 2 the low (no-drain) state of a
cell disappears, and the drain ignites, once g(A) > J_K / (2 sqrt(c0 eta)), g(A) = A / (1 + A / K_e).
J_K is therefore set by the ignition level, with the same rule as the main line's threshold:
  J_K = 2 sqrt(c0 eta) g(theta_ign * A_free),  theta_ign = 0.82, A_free = 4.0 (sink-free ring level).
competent = cell in the competent ring, or already a drain (c > eta / 2), so drains are started only in the
ring (as the main line only places primordia there) but persist as cells are displaced outwards.
A drain cell also drains its inner compartment to the vasculature (eta2 * c / eta) and attracts PIN as a
primordium does (cue A_q * c / eta). Daughter cells inherit c.

Initiation events are only recorded (for statistics), never imposed: a new primordium is logged when a
connected group of cells first exceeds c = eta / 2 at least r_log cells from every logged primordium.
"""
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frozen_v2"))
from layer import TwoLayerSim  # noqa: E402

CANAL_DEFAULTS = dict(tau_can=2.0, theta_ign=0.82, hill=2.0, r_log=2.0, c0_frac=0.01, A_free=4.0, J_K=None)


class CanalSim(TwoLayerSim):
    def __init__(self, params, ramp=None):
        self.c = None
        self.logged = []                                       # (x, y) of logged primordia, moved with the tissue
        p = dict(CANAL_DEFAULTS)
        p.update(params)
        p.update(Th=1e9, k_I=0.0)                              # no placed primordia, no secondary field
        super().__init__(p, ramp)
        self.c = np.full(self.tis.n, self.p["c0_frac"] * self.p["eta"])
        grow = self.tis.grow                                   # TwoLayerSim's wrapper (carries A2)

        def grow_and_carry(g):
            parent = grow(g)
            if self.c is not None:
                self.c = self.c[parent]
            self.logged = [(x * g, y * g) for x, y in self.logged]
            return parent

        self.tis.grow = grow_and_carry

    def _g(self, A):
        p = self.p
        return A / (1.0 + A / p["K_e"]) if p["K_e"] > 0 else A

    def _step(self, A):
        p, G = self.p, self.G
        n = G["n"]
        c0 = p["c0_frac"] * p["eta"]
        if self.c is None or len(self.c) != n:
            self.c = np.full(n, c0)
        if self.A2 is None or len(self.A2) != n:
            self.A2 = np.zeros(n)
        if p["J_K"] is None:                                   # flux scale from the sink-free ring level (a rule, no pattern data)
            g_ign = float(self._g(np.array([p["theta_ign"] * p["A_free"]]))[0])
            p["J_K"] = 2.0 * np.sqrt(c0 * p["eta"]) * g_ign
        J = self.c * self._g(A)                                # flux carried by the drain itself
        ring = (self.rad >= p["R_c"]) & (self.rad < p["R_p"])
        competent = ring | (self.c > 0.5 * p["eta"])
        h = p["hill"]
        target = c0 + p["eta"] * J ** h / (p["J_K"] ** h + J ** h) * competent
        G["eta_lin"] = self.c                                 # read by TwoLayerSim._step as the transfer coefficient
        G["cue"] = p["A_q"] * self.c / p["eta"]
        self.vasc = p["eta2"] * self.c / p["eta"]
        A_new = super()._step(A)
        self.c = self.c + p["dt"] * (target - self.c) / p["tau_can"]
        return A_new

    def _geometry(self, first=False):
        super()._geometry(first)
        if first or self.c is None or len(self.c) != self.tis.n:
            return
        p, pts = self.p, self.tis.pts
        on = self.c > 0.5 * p["eta"]
        if not on.any():
            return
        # group drain cells into connected clusters and log clusters far from every logged primordium
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
        for g in groups.values():
            w = self.c[g]
            x, y = float((w * pts[g, 0]).sum() / w.sum()), float((w * pts[g, 1]).sum() / w.sum())
            if all(math.hypot(x - lx, y - ly) > p["r_log"] for lx, ly in self.logged):
                self.logged.append((x, y))
                self.log.append((self.t, x, y))
