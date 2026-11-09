"""Structural change 3: cell-to-cell variation in PIN amount (PROTOCOL.md), and the local-residual statistic that
sets its amplitude. The frozen main line is used unchanged; the noise is added in a subclass.
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "frozen_v2"))
from layer import TwoLayerSim  # noqa: E402


class NoisySim(TwoLayerSim):
    """PIN amount of each cell multiplied by xi = exp(sigma z - sigma^2 / 2); both daughters redraw at division."""

    def __init__(self, params, ramp=None):
        self.xi = None
        self._nrng = np.random.default_rng(int(params.get("seed", 1)) + 104729)     # separate stream
        super().__init__(params, ramp)
        grow = self.tis.grow                                                        # TwoLayerSim's wrapper

        def grow_and_redraw(g):
            parent = grow(g)
            if self.xi is not None:
                divided = np.bincount(parent, minlength=len(self.xi))[parent] > 1    # mother index appears twice
                xi = self.xi[parent]
                xi[divided] = self._draw(int(divided.sum()))
                self.xi = xi
            return parent

        self.tis.grow = grow_and_redraw

    def _draw(self, n):
        s = self.p.get("sigma_pin", 0.0)
        return np.exp(s * self._nrng.standard_normal(n) - 0.5 * s * s)

    def _geometry(self, first=False):
        super()._geometry(first)
        if self.xi is None or len(self.xi) != self.tis.n:
            self.xi = self._draw(self.tis.n)
        self.G["Pcell"] = self.G["Pcell"] * self.xi


def residual_sd(pos_um, logv, value, radius_um, band=(15.0, 50.0), r_nb=7.0, min_nb=3, extra_mask=None):
    """Local residual of log values against the mean of neighbours within r_nb (um), for cells in the radial band
    whose value is above the band median. Returns the pooled residuals and the mean neighbour count."""
    inband = (radius_um >= band[0]) & (radius_um <= band[1])
    if inband.sum() < 10:
        return np.array([]), 0.0
    keep = inband & (value > np.median(value[inband]))          # median over the whole band, as in the protocol
    if extra_mask is not None:
        keep &= extra_mask
    sel = np.where(keep)[0]
    tree = cKDTree(pos_um)
    res, ks = [], []
    for i, nb in zip(sel, tree.query_ball_point(pos_um[sel], r_nb)):
        nb = [j for j in nb if j != i]
        if len(nb) >= min_nb:
            res.append(logv[i] - logv[nb].mean())
            ks.append(len(nb))
    return np.array(res), (float(np.mean(ks)) if ks else 0.0)


def s_from(res, kbar):
    return float(np.std(res) / np.sqrt(1.0 + 1.0 / kbar)) if len(res) > 5 else float("nan")
