"""Growing, dividing L1 cell sheet (top view of the shoot apex).

Cells are Voronoi regions of material points. Growth is a uniform dilation about
the apex centre, so cells flow outward through fixed radial zones; cells divide
above an area threshold and leave the domain at R_out. This replaces the fixed
mesh of the first spike, whose frozen irregularities dominated the results.
"""
import math
import numpy as np
from scipy.spatial import Voronoi


def _ghost_ring(R):
    n = int(round(2 * math.pi * R))
    t = 2 * math.pi * np.arange(n) / n
    return R * np.c_[np.cos(t), np.sin(t)]


class Tissue:
    def __init__(self, R_out, seed=1, v_div=1.5, lloyd=0.25, relax_iters=40):
        self.R_out, self.v_div, self.lloyd = float(R_out), float(v_div), float(lloyd)
        self.rng = np.random.default_rng(seed)
        n = int(round(math.pi * R_out ** 2))          # mean cell area ~ 1
        r = R_out * np.sqrt(self.rng.random(n))
        t = 2 * math.pi * self.rng.random(n)
        self.pts = np.c_[r * np.cos(t), r * np.sin(t)]
        self.tessellate()
        for _ in range(relax_iters):
            self.pts += 0.8 * (self.cent - self.pts)
            rr = np.hypot(self.pts[:, 0], self.pts[:, 1])
            far = rr > R_out - 0.2
            self.pts[far] *= ((R_out - 0.2) / rr[far])[:, None]
            self.tessellate()

    # -- geometry of the current configuration ------------------------------
    def tessellate(self):
        n = len(self.pts)
        P = np.vstack([self.pts, _ghost_ring(self.R_out + 0.8)])
        vor = Voronoi(P)
        rp = vor.ridge_points
        rv = np.asarray(vor.ridge_vertices)
        ok = (rv >= 0).all(1)
        a, b = rp[ok, 0], rp[ok, 1]
        va, vb = vor.vertices[rv[ok, 0]], vor.vertices[rv[ok, 1]]
        L = np.hypot(va[:, 0] - vb[:, 0], va[:, 1] - vb[:, 1])
        i = np.r_[a, b]; j = np.r_[b, a]; L2 = np.r_[L, L]
        VA = np.vstack([va, va]); VB = np.vstack([vb, vb])
        dij = np.hypot(P[i, 0] - P[j, 0], P[i, 1] - P[j, 1])
        ta = L2 * dij / 4.0                           # triangle (x_i, v_a, v_b)
        area = np.bincount(i, ta, len(P))
        safe = np.maximum(area, 1e-12)
        cx = np.bincount(i, ta * (P[i, 0] + VA[:, 0] + VB[:, 0]) / 3.0, len(P)) / safe
        cy = np.bincount(i, ta * (P[i, 1] + VA[:, 1] + VB[:, 1]) / 3.0, len(P)) / safe
        self.area = area[:n]
        self.cent = np.c_[cx, cy][:n]
        m = (i < n) & (j < n) & (L2 > 1e-6)
        self.src, self.dst, self.l, self.d = i[m], j[m], L2[m], dij[m]
        self.n = n

    # -- one growth increment -------------------------------------------------
    def grow(self, g):
        """Dilate by factor g, divide, drop cells beyond R_out, re-tessellate.

        Returns `parent`, an index array such that new_state = old_state[parent]
        (daughters inherit the mother's concentrations).
        """
        self.pts += self.lloyd * (self.cent - self.pts)
        self.pts *= g
        area = self.area * g * g
        rad = np.hypot(self.pts[:, 0], self.pts[:, 1])
        keep = rad <= self.R_out
        md = np.where(keep & (area > self.v_div))[0]
        ang = math.pi * self.rng.random(len(md))
        off = (0.28 * np.sqrt(area[md]))[:, None] * np.c_[np.cos(ang), np.sin(ang)]
        new = self.pts[md] + off
        self.pts[md] -= off
        ik = np.where(keep)[0]
        parent = np.r_[ik, md]
        self.pts = np.vstack([self.pts[ik], new])
        self.tessellate()
        return parent

    def polygons(self):
        """Cell polygons for plotting (slow path, not used in the solver)."""
        P = np.vstack([self.pts, _ghost_ring(self.R_out + 0.8)])
        vor = Voronoi(P)
        return [vor.vertices[vor.regions[vor.point_region[k]]] for k in range(len(self.pts))]


def ring_graph(n):
    """1D periodic chain of n unit cells, for solver verification."""
    i = np.arange(n)
    src = np.r_[i, i]
    dst = np.r_[(i + 1) % n, (i - 1) % n]
    return src, dst, np.ones(2 * n), np.ones(2 * n), np.ones(n)
