"""Solver checks that do not depend on any biological claim."""
import math
import numpy as np
from model import DEFAULT, Sim, rhs
from tissue import Tissue, ring_graph


def graph_from(src, dst, l, d, V, p, rho=0.0, mu=0.0):
    n = len(V)
    return dict(src=src, dst=dst, n=n, lw=l, Dl=p["D"] * l / d, V=V, Pcell=p["p0"] * V, beta=math.log(p["b"]),
                rho=np.full(n, rho), srcp=np.zeros(n), mu=mu, cue=np.zeros(n), eta_lin=np.zeros(n),
                eta_cap=np.zeros(n))


def test_conservation():
    p = dict(DEFAULT)
    tis = Tissue(10.0, seed=3)
    G = graph_from(tis.src, tis.dst, tis.l, tis.d, tis.area, p)
    rng = np.random.default_rng(0)
    A = 7.0 * (1 + 0.3 * rng.random(tis.n))
    m0 = (A * tis.area).sum()
    inst = abs((rhs(A, G, p) * tis.area).sum()) / m0
    for _ in range(3000):
        A = A + 0.005 * rhs(A, G, p)
    drift = abs((A * tis.area).sum() - m0) / m0
    print(f"[conservation] cells={tis.n} instantaneous net flux/mass={inst:.2e} drift after 3000 steps={drift:.2e} "
          f"min A={A.min():.3f}")
    assert inst < 1e-12 and drift < 1e-10


def test_ring(D, n=60, seed=1):
    """Compare simulated pattern onset on a 1D ring with the linearised operator."""
    p = dict(DEFAULT); p["D"] = D
    src, dst, l, d, V = ring_graph(n)
    rho, mu, k = p["rho_pz"], p["mu"], p["kappa_A"]
    G = graph_from(src, dst, l, d, V, p, rho=rho, mu=mu)
    A0 = (-1 + math.sqrt(1 + 4 * k * rho / mu)) / (2 * k)
    base = np.full(n, A0)
    f0 = rhs(base, G, p)
    J = np.zeros((n, n)); h = 1e-6
    for c in range(n):
        e = base.copy(); e[c] += h
        J[:, c] = (rhs(e, G, p) - f0) / h
    ev, vec = np.linalg.eig(J)
    kmax = int(np.argmax(ev.real))
    lam = ev.real[kmax]
    mode = int(np.argmax(np.abs(np.fft.rfft(vec[:, kmax].real))[1:]) + 1)
    A = base * (1 + 1e-4 * np.random.default_rng(seed).standard_normal(n))
    amp0 = A.std()
    tlin = 6.0 / max(lam, 0.05)                      # a few e-foldings, still linear
    for _ in range(int(tlin / 0.002)):
        A = A + 0.002 * rhs(A, G, p)
    spec = np.abs(np.fft.rfft(A - A.mean()))[1:]
    sim_mode = int(np.argmax(spec) + 1)
    growth = math.log(A.std() / amp0) / tlin
    print(f"[ring D={D:5.1f}] residual at uniform state={np.abs(f0).max():.1e} max eigenvalue={lam:+.4f} "
          f"predicted mode={mode} | simulated growth rate={growth:+.4f} dominant mode={sim_mode}")
    return lam, mode, growth, sim_mode


def test_tissue():
    tis = Tissue(12.0, seed=1)
    n0 = tis.n
    g = math.exp(0.03 * 0.25)
    hist = []
    for k in range(1200):
        tis.grow(g)
        if k % 100 == 99:
            hist.append((tis.n, tis.area.mean(), tis.area.std() / tis.area.mean(), tis.area.sum() / (math.pi * 144),
                         np.bincount(tis.src, minlength=tis.n).mean()))
    h = np.array(hist)
    print(f"[tissue] cells start={n0} then min/max={int(h[:,0].min())}/{int(h[:,0].max())} mean area={h[:,1].mean():.3f} "
          f"area CV={h[:,2].mean():.3f} covered/disc={h[:,3].mean():.3f} mean neighbours={h[:,4].mean():.2f}")
    assert 0.8 < h[:, 1].mean() < 1.3 and abs(h[:, 4].mean() - 6) < 0.4


if __name__ == "__main__":
    test_conservation()
    lam1, m1, g1, s1 = test_ring(4.0)
    lam2, m2, g2, s2 = test_ring(40.0)
    assert lam1 > 0 and g1 > 0 and abs(g1 - lam1) / lam1 < 0.25 and abs(s1 - m1) <= 1
    assert lam2 < 0 and g2 < 0
    test_tissue()
    s = Sim(dict(t_end=20.0)).run(verbose=True)
    print("ALL CHECKS PASSED")
