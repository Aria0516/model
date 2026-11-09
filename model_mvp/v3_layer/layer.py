"""Two-layer extension: an inner compartment under every epidermal cell (structural change 2).

The epidermal primordium 'sink' now transfers auxin into the inner layer (saturable, K_e) instead
of removing it; the inner layer has lateral diffusion, turnover, passive exchange with the
epidermis (k_v) and a vascular drain under primordia (eta2). Implemented as a subclass so that
model.py and frozen_v1 stay unchanged.
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model import Sim, rhs  # noqa: E402

LAYER_DEFAULTS = dict(k_v=0.3, K_e=0.0, eta2=3.0, D2=None)   # K_e = 0 means linear transfer


class TwoLayerSim(Sim):
    def __init__(self, params, ramp=None):
        self._ramp = ramp
        self.A2 = None
        self.vasc = None
        p = dict(LAYER_DEFAULTS)
        p.update(params)
        super().__init__(p)
        self.A2 = np.zeros(self.tis.n)                        # inner layer starts empty after any calibration
        self.track2 = {}
        grow = self.tis.grow

        def grow_and_carry(g):
            parent = grow(g)
            self.A2 = self.A2[parent]
            return parent

        self.tis.grow = grow_and_carry

    def _geometry(self, first=False):
        r = self._ramp
        if r is not None:
            f = min(max(self.t / r["T"], 0.0), 1.0)
            rc = r["rc0"] + f * (r["rc1"] - r["rc0"])
            self.p.update(R_c=rc, R_p=rc + 2.0, R_src=rc + 2.0 + r["ds"], rho_far=r["rho0"] + f * (r["rho1"] - r["rho0"]))
        super()._geometry(first)
        pts, n, p = self.tis.pts, self.tis.n, self.p
        vasc = np.zeros(n)
        for q in self.prim:                                  # vascular drain under each primordium (q["vasc"] can switch it off)
            d2 = (pts[:, 0] - q["x"]) ** 2 + (pts[:, 1] - q["y"]) ** 2
            np.add(vasc, p["eta2"] * q.get("vasc", 1.0) * np.exp(-d2 / (2 * p["w"] ** 2)), out=vasc)
        self.vasc = vasc
        if p.get("track") and self.A2 is not None and len(self.A2) == n:
            for q in self.prim:
                k = int(np.argmin((pts[:, 0] - q["x"]) ** 2 + (pts[:, 1] - q["y"]) ** 2))
                self.track2.setdefault(q["id"], []).append((self.t, float(self.A2[k])))

    def _step(self, A):
        p, G = self.p, self.G
        n = G["n"]
        if self.A2 is None or len(self.A2) != len(A):
            self.A2 = np.zeros(len(A))
        if self.vasc is None or len(self.vasc) != n:
            self.vasc = np.zeros(n)
        A2 = self.A2
        Gx = dict(G)
        Gx["eta_lin"] = np.zeros(n)                          # epidermal loss now goes through the transfer below
        transfer = G["eta_lin"] * (A / (1.0 + A / p["K_e"]) if p["K_e"] > 0 else A)
        exch = p["k_v"] * (A - A2)
        src, dst = G["src"], G["dst"]
        D2 = p["D"] if p["D2"] is None else p["D2"]
        lat = np.bincount(src, (D2 / p["D"]) * G["Dl"] * (A2[dst] - A2[src]), n) / G["V"]
        dA1 = rhs(A, Gx, p) - transfer - exch
        dA2 = transfer + exch + lat - G["mu"] * A2 - self.vasc * A2
        self.A2 = np.maximum(A2 + p["dt"] * dA2, 0.0)
        A = np.maximum(A + p["dt"] * dA1, 0.0)
        if p["cz_mix"]:
            V = G["V"]
            A[self.cz] = (A[self.cz] * V[self.cz]).sum() / V[self.cz].sum()
        return A
