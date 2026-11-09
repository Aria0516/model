"""Auxin-PIN1 phyllotaxis model, version 1 (session scratch build).

Core loop (always on)
  auxin production/turnover, passive exchange, PIN1-mediated transport, with a
  finite PIN pool per cell allocated up the auxin gradient
      Smith et al. 2006 (exponential allocation, quadratic saturating flux)
      Jonsson et al. 2006 / Sahlin et al. 2009 (competition for a finite pool)
  primordia initiate where auxin crosses a threshold in a competent ring; they
  travel outward with the tissue and drain auxin into inner tissue (Smith 2006).

Switchable modules (off by default)
  M2  central-zone reservoir + centripetal PIN bias  (Barbier de Reuille 2006;
      Galvan-Ampudia 2020 Figs 1,3): pin_cz, rho_cz, kappa_c
  M3  primordia turn from sink to source with age     (Galvan-Ampudia 2020 Fig 3):
      sink_age_off, src_age_on, rho_src, cue_age_off
  M4  leaky temporal integration and DR5-like read-out (Galvan-Ampudia 2020
      Figs 4-6): tau_M, tau_R, in_loop
  M5  transient secondary inhibitory field emitted by young primordia that
      raises the initiation threshold nearby (Besnard 2014): k_I, w_I, tau_I

No divergence angle, plastochron or handedness is prescribed anywhere.
Units: length = one cell diameter, time = arbitrary (plastochron is emergent).
"""
import math
import time
import numpy as np

from tissue import Tissue

DEFAULT = dict(
    # geometry and growth
    R_out=12.0, R_c=4.0, R_p=6.0, gamma=0.03, v_div=1.5, lloyd=0.25,
    mesh_seed=1, seed=1, dt=0.01, n_geo=25, t_end=450.0, dilution=1,
    # auxin turnover and passive exchange
    rho_pz=18.0, rho_cz=9.0, rho_prox=9.0, kappa_A=1.0, mu=0.3, D=4.0,
    # PIN1 allocation and active transport
    T=22.5, kappa_T=1.0, expo=2.0, p0=0.94, b=3.0, rho0=0.0,
    # primordia
    Th=8.5, r_ex=3.0, w=2.0, sink_mode="linear", eta=3.0, A_cap=10.0, A_q=8.0, avg_nb=0,
    Th_rel=0.0, t_cal=30.0,
    # M2 central zone
    pin_cz=1.0, kappa_c=0.0,
    # M3 age-dependent role of primordia (ages in model time units)
    sink_age_off=1e9, sink_tau=7.5, cue_age_off=1e9, cue_tau=7.5,
    src_age_on=1e9, src_tau=7.5, rho_src=0.0,
    # M4 read-out
    tau_M=0.0, in_loop=0, tau_R=0.0, theta_M=6.0, delta_M=0.4,
    # M5 secondary inhibitory field on the initiation decision (Besnard et al. 2014): strength, range, lifetime
    k_I=0.0, w_I=8.0, tau_I=6.0, rise_I=0.0,
    # how the position of a new primordium is fixed: "instant" (first cell over threshold),
    # "patch" (wait for n_patch connected cells, use their centroid), "track" (follow the maximum for tau_c)
    commit="instant", n_patch=5, r_patch=2.2, tau_c=3.0, r_track=2.5,
    # primordium footprint grows with age: w(age) = w * exp(w_grow * gamma * age), capped at w * w_cap
    w_grow=0.0, w_cap=3.0,
    # central zone as a well-mixed auxin pool shared by all ring positions; D_x scales exchange across its border
    cz_mix=0, D_x=1.0,
    # start-up
    init_frac=0.5, noise=0.01, start="noise",
    # recording
    snap_dt=0.0, track=0,
)


def rhs(A, G, p):
    """dA/dt on a fixed cell graph. Fluxes are antisymmetric, so transport conserves mass."""
    src, dst, n = G["src"], G["dst"], G["n"]
    C = p.get("fb_auxin", 1.0) * A + G["cue"]
    E = np.exp(np.clip(G["beta"] * (C - 10.0), -50.0, 50.0))
    w = G["lw"] * E[dst]
    den = np.bincount(src, w, n) + p["rho0"]
    Pij = G["Pcell"][src] * w / den[src]
    u = A ** p["expo"]
    F = p["T"] * Pij * u[src] / (1.0 + p["kappa_T"] * u[dst])
    out = np.bincount(src, F + G["Dl"] * (A[src] - A[dst]), n) - np.bincount(dst, F, n)
    prod = (G["rho"] + G["srcp"]) / (1.0 + p["kappa_A"] * A)
    sink = G["eta_lin"] * A + G["eta_cap"] * np.maximum(A - p["A_cap"], 0.0)
    return prod - G["mu"] * A - sink - out / G["V"]


def pin_vectors(A, G, p):
    """Mean PIN1 direction per cell (unit-weighted by wall PIN), for plots and statistics."""
    src, dst, n = G["src"], G["dst"], G["n"]
    C = p.get("fb_auxin", 1.0) * A + G["cue"]
    E = np.exp(np.clip(G["beta"] * (C - 10.0), -50.0, 50.0))
    w = G["lw"] * E[dst]
    frac = w / (np.bincount(src, w, n) + p["rho0"])[src]
    ux, uy = G["ex"], G["ey"]
    return np.c_[np.bincount(src, frac * ux, n), np.bincount(src, frac * uy, n)]


def _decay(age, off, tau):
    return 1.0 if age <= off else math.exp(-(age - off) / tau)


def _ramp(age, on, tau):
    return 0.0 if age <= on else 1.0 - math.exp(-(age - on) / tau)


class Sim:
    def __init__(self, params=None):
        p = dict(DEFAULT)
        p.update(params or {})
        self.p = p
        self.tis = Tissue(p["R_out"], p["mesh_seed"], p["v_div"], p["lloyd"])
        self.rng = np.random.default_rng(p["seed"])
        self.t = 0.0
        self.prim, self.log, self.snaps, self.track, self.kymo = [], [], [], {}, []
        self.inc = []                                  # incipient sites whose position is not fixed yet
        self.ghost_sum, self.ring_mean_sum, self.geo_count = 0, 0.0, 0
        nbins = int(p["R_out"]) + 1
        self.dg_prof, self.dg_in, self.dg_in_free, self.dg_n = np.zeros(nbins), np.zeros(nbins), np.zeros(nbins), 0
        self.mu_tot = p["mu"] + (2.0 * p["gamma"] if p["dilution"] else 0.0)
        rad = np.hypot(self.tis.pts[:, 0], self.tis.pts[:, 1])
        rho = self._rho(rad)
        k = p["kappa_A"]
        A0 = (-1 + np.sqrt(1 + 4 * k * rho / self.mu_tot)) / (2 * k) if k > 0 else rho / self.mu_tot
        self.A = p["init_frac"] * A0 * (1 + p["noise"] * self.rng.standard_normal(len(A0)))
        self.M = self.A.copy()
        self.R = np.zeros_like(self.A)
        if p["start"] == "pair":                       # cotyledon-like opposite pair
            rg = 0.5 * (p["R_c"] + p["R_p"])
            for sgn in (1.0, -1.0):
                self._add_primordium(sgn * rg, 0.0)
        elif p["start"] == "whorl3":
            rg = 0.5 * (p["R_c"] + p["R_p"])
            for k3 in range(3):
                a = 2 * math.pi * k3 / 3
                self._add_primordium(rg * math.cos(a), rg * math.sin(a))
        if p["Th_rel"] > 0:
            # set the threshold as a fraction of the sink-free auxin level in the ring, so that
            # changing transport or turnover parameters does not silently move the operating point
            seeded, self.prim = self.prim, []
            keep_start, p["start"] = p["start"], "seeded"          # no initiation during calibration
            self._geometry(first=True)
            A = self.A.copy()
            for _ in range(int(p["t_cal"] / p["dt"])):
                A = self._step(A)
            ring = (self.rad >= p["R_c"]) & (self.rad < p["R_p"])
            self.free_level = float(A[ring].mean())
            p["Th"] = p["Th_rel"] * self.free_level
            self.prim, p["start"] = seeded, keep_start
            self.ghost_sum, self.ring_mean_sum, self.geo_count = 0, 0.0, 0
        self._geometry(first=True)

    # -- helpers ---------------------------------------------------------------
    def _rho(self, rad):
        p = self.p
        rho = np.where((rad >= p["R_c"]) & (rad < p["R_p"]), p["rho_pz"], p["rho_prox"])
        rho[rad < p["R_c"]] = p["rho_cz"]
        return rho.astype(float)

    def _add_primordium(self, x, y, t0=None):
        # t0: time of the initiation decision (starts the secondary field);
        # tc: time the position is fixed and the sink and polarity cue switch on
        q = dict(x=float(x), y=float(y), t0=self.t if t0 is None else t0, tc=self.t, id=len(self.log))
        self.prim.append(q)
        self.log.append((self.t, float(x), float(y)))
        return q

    def _step(self, A):
        """One explicit chemistry step; optionally the central zone is a well-mixed pool."""
        p = self.p
        A = np.maximum(A + p["dt"] * rhs(A, self.G, p), 0.0)
        if p["cz_mix"]:
            V = self.G["V"]
            A[self.cz] = (A[self.cz] * V[self.cz]).sum() / V[self.cz].sum()
        return A

    def _geometry(self, first=False):
        p, tis = self.p, self.tis
        if not first:
            g = math.exp(p["gamma"] * p["dt"] * p["n_geo"])
            parent = tis.grow(g)
            self.A, self.M, self.R = self.A[parent], self.M[parent], self.R[parent]
            for q in self.prim + self.inc:
                q["x"] *= g; q["y"] *= g
            lim = p["R_out"] + 3 * p["w"]
            self.prim = [q for q in self.prim if math.hypot(q["x"], q["y"]) <= lim]
        pts, n = tis.pts, tis.n
        rad = np.hypot(pts[:, 0], pts[:, 1])
        cz = rad < p["R_c"]
        ring = (rad >= p["R_c"]) & (rad < p["R_p"])
        eta = np.zeros(n); cue = np.zeros(n); srcp = np.zeros(n); inh = np.zeros(n)
        dmin = np.full(n, np.inf)

        dinc = np.full(n, np.inf)                      # distance to the nearest incipient site

        def field(q, d2):
            if p["k_I"] > 0:                           # M5: transient field that raises the initiation threshold
                af = self.t - q["t0"]
                rise = 1.0 if p["rise_I"] <= 0 else 1.0 - math.exp(-af / p["rise_I"])    # delayed onset
                np.add(inh, p["k_I"] * rise * math.exp(-af / p["tau_I"]) * np.exp(-d2 / (2 * p["w_I"] ** 2)), out=inh)

        def stamp(q):
            age = self.t - q["tc"]
            d2 = (pts[:, 0] - q["x"]) ** 2 + (pts[:, 1] - q["y"]) ** 2
            wm = p["w"] * min(math.exp(p["w_grow"] * p["gamma"] * age), p["w_cap"])   # footprint may grow with age
            s = np.exp(-d2 / (2 * wm ** 2))
            # q["sink"] / q["cue"] (default 1) let an experiment switch off one primordium's sink or cue
            np.add(eta, p["eta"] * q.get("sink", 1.0) * _decay(age, p["sink_age_off"], p["sink_tau"]) * s, out=eta)
            np.maximum(cue, p["A_q"] * q.get("cue", 1.0) * _decay(age, p["cue_age_off"], p["cue_tau"]) * s, out=cue)
            np.add(srcp, p["rho_src"] * _ramp(age, p["src_age_on"], p["src_tau"]) * s, out=srcp)
            field(q, d2)
            np.minimum(dmin, np.sqrt(d2), out=dmin)

        def reserve(q):                                # incipient site: no sink yet, only field and exclusion
            d2 = (pts[:, 0] - q["x"]) ** 2 + (pts[:, 1] - q["y"]) ** 2
            field(q, d2)
            np.minimum(dinc, np.sqrt(d2), out=dinc)

        for q in self.prim:
            stamp(q)
        # initiation: competent ring, above threshold, not on an existing primordium
        if not first or p["start"] == "noise":
            X = self.M if (p["tau_M"] > 0 and p["in_loop"]) else self.A
            for _ in range(int(p["avg_nb"])):          # founder-group read-out: average over a cell and its neighbours
                X = (tis.area * X + np.bincount(tis.src, tis.area[tis.dst] * X[tis.dst], n)) / (
                    tis.area + np.bincount(tis.src, tis.area[tis.dst], n))
            mode = p["commit"]
            if mode == "track":
                # the site follows the local auxin maximum for tau_c before its position is fixed
                still = []
                for q in self.inc:
                    near = np.hypot(pts[:, 0] - q["x"], pts[:, 1] - q["y"]) < p["r_track"]
                    wgt = np.maximum(X[near] - 0.9 * p["Th"], 0.0)
                    if wgt.sum() > 0:
                        c = (wgt[:, None] * pts[near]).sum(0) / wgt.sum()
                        q["x"], q["y"] = float(c[0]), float(c[1])
                    if self.t - q["t0"] >= p["tau_c"]:
                        stamp(self._add_primordium(q["x"], q["y"], t0=q["t0"]))
                    else:
                        still.append(q); reserve(q)
                self.inc = still
            while True:
                ok = ring & (X - inh >= p["Th"]) & (dmin > p["r_ex"]) & (dinc > p["r_ex"])
                if not ok.any():
                    break
                if mode == "patch":
                    # wait until a compact group of cells around a peak is above threshold, then place
                    # the centre at the excess-weighted centroid of that group. The group is taken within
                    # r_patch of the peak cell so that the centre always lies on the group itself.
                    exc = X - inh - p["Th"]
                    cand = np.where(ok)[0]
                    placed = False
                    for i in cand[np.argsort(-exc[cand])]:
                        loc = ok & (np.hypot(pts[:, 0] - pts[i, 0], pts[:, 1] - pts[i, 1]) < p["r_patch"])
                        if loc.sum() >= p["n_patch"]:
                            wgt = exc[loc] + 1e-9
                            c = (wgt[:, None] * pts[loc]).sum(0) / wgt.sum()
                            stamp(self._add_primordium(c[0], c[1]))
                            placed = True
                            break
                    if not placed:
                        break
                    continue
                idx = np.where(ok)[0]
                i = idx[np.argmax(X[idx])]
                near = np.hypot(pts[:, 0] - pts[i, 0], pts[:, 1] - pts[i, 1]) < 1.6
                wgt = np.maximum(X[near] - 0.8 * X[i], 0.0)
                c = (wgt[:, None] * pts[near]).sum(0) / wgt.sum()
                if mode == "track":
                    q = dict(x=float(c[0]), y=float(c[1]), t0=self.t)
                    self.inc.append(q); reserve(q)
                else:
                    stamp(self._add_primordium(c[0], c[1]))
        src, dst = tis.src, tis.dst
        ex = (pts[dst, 0] - pts[src, 0]) / tis.d
        ey = (pts[dst, 1] - pts[src, 1]) / tis.d
        lw = tis.l.copy()
        if p["kappa_c"] != 0.0:                        # tissue-scale centripetal polarity cue
            rs = np.maximum(rad[src], 1e-9)
            inward = -(ex * pts[src, 0] + ey * pts[src, 1]) / rs
            lw = lw * np.exp(p["kappa_c"] * inward * (rad[src] > 1.0))
        lin = p["sink_mode"] == "linear"
        self.G = dict(
            src=src, dst=dst, n=n, lw=lw, V=tis.area,
            Dl=p["D"] * tis.l / tis.d * np.where(cz[src] != cz[dst], p["D_x"], 1.0),   # exchange with the central zone
            Pcell=p["p0"] * tis.area * np.where(cz, p["pin_cz"], 1.0), beta=math.log(p["b"]),
            rho=self._rho(rad), srcp=srcp, mu=self.mu_tot, cue=cue,
            eta_lin=eta if lin else np.zeros(n), eta_cap=np.zeros(n) if lin else eta,
            ex=ex, ey=ey,
        )
        self.rad, self.comp, self.cz = rad, (~cz).astype(float), cz
        # auxin peaks that are not primordia (uncontrolled accumulations outside the ring)
        self.ghost_sum += int(((self.A >= p["Th"]) & (dmin > p["r_ex"]) & ~ring).sum())
        self.ring_mean_sum += float(self.A[ring].mean()); self.geo_count += 1
        if p.get("diag") and self.t > p["t_end"] / 3 and self.geo_count % 4 == 0:
            # radial auxin profile and how centripetal the PIN field is (Galvan-Ampudia 2020, Fig 3)
            nb = int(p["R_out"]) + 1
            rb = np.minimum(rad.astype(int), nb - 1)
            cnt = np.maximum(np.bincount(rb, minlength=nb), 1)
            pv = pin_vectors(self.A, self.G, p)
            inward = -(pv[:, 0] * pts[:, 0] + pv[:, 1] * pts[:, 1]) / np.maximum(rad, 1e-9)
            free = dmin > 2 * p["w"]                    # cells not under a primordium footprint
            self.dg_prof += np.bincount(rb, self.A, nb) / cnt
            self.dg_in += np.bincount(rb, inward, nb) / cnt
            self.dg_in_free += np.bincount(rb[free], inward[free], nb) / np.maximum(np.bincount(rb[free], minlength=nb), 1)
            self.dg_n += 1
        if p.get("kymo"):                              # auxin along the competent ring vs time
            nb = 72
            b = (np.degrees(np.arctan2(pts[ring, 1], pts[ring, 0])) % 360 // (360 / nb)).astype(int)
            cnt = np.maximum(np.bincount(b, minlength=nb), 1)
            self.kymo.append((self.t, np.bincount(b, self.A[ring], nb) / cnt,
                              np.array([np.max(self.A[ring][b == k], initial=0.0) for k in range(nb)])))
        if p["track"]:
            for q in self.prim:
                k = int(np.argmin((pts[:, 0] - q["x"]) ** 2 + (pts[:, 1] - q["y"]) ** 2))
                self.track.setdefault(q["id"], []).append(
                    (self.t, math.hypot(q["x"], q["y"]), float(self.A[k]), float(self.M[k]), float(self.R[k])))

    # -- time stepping ---------------------------------------------------------
    def run(self, verbose=False):
        p = self.p
        dt, n_geo = p["dt"], p["n_geo"]
        steps = int(round(p["t_end"] / dt))
        next_snap = 0.0
        t0 = time.time()
        for s in range(steps):
            self.t = s * dt
            if s and s % n_geo == 0:
                self._geometry()
            if p["snap_dt"] and self.t >= next_snap:
                next_snap += p["snap_dt"]
                self.snaps.append(dict(t=self.t, pts=self.tis.pts.copy(), A=self.A.copy(), R=self.R.copy(),
                                       M=self.M.copy(), pin=pin_vectors(self.A, self.G, p),
                                       prim=[(q["x"], q["y"], q["id"], self.t - q["t0"]) for q in self.prim]))
            self.A = self._step(self.A)
            if p["tau_M"] > 0:
                self.M += dt * (self.A - self.M) / p["tau_M"]
            else:
                self.M = self.A
            if p["tau_R"] > 0:
                H = 1.0 / (1.0 + np.exp(-(self.M - p["theta_M"]) / p["delta_M"]))
                self.R += dt * (self.comp * H - self.R) / p["tau_R"]
            if not np.isfinite(self.A).all():
                raise FloatingPointError(f"blow-up at t={self.t:.2f}")
        self.wall = time.time() - t0
        if verbose:
            print(f"cells={self.tis.n} primordia={len(self.log)} wall={self.wall:.1f}s "
                  f"A[min,mean,max]=[{self.A.min():.2f},{self.A.mean():.2f},{self.A.max():.2f}]")
        return self
