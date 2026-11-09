"""Linear stability of the uniform state on a 1D ring: growth rate and wavelength vs parameters.

Tells us how far above the patterning threshold the competent zone operates and
what spacing (in cells) the transport feedback alone would select.
"""
import math
import sys
import numpy as np
from model import DEFAULT, rhs
from tests import graph_from
from tissue import ring_graph


def analyse(p, A_level=None, n=120):
    src, dst, l, d, V = ring_graph(n)
    mu = p["mu"] + 2 * p["gamma"]
    k = p["kappa_A"]
    A0 = (-1 + math.sqrt(1 + 4 * k * p["rho_pz"] / mu)) / (2 * k)
    if A_level is not None:                          # hold the level by adjusting production
        A0 = A_level
        rho = mu * A0 * (1 + k * A0)
    else:
        rho = p["rho_pz"]
    G = graph_from(src, dst, l, d, V, p, rho=rho, mu=mu)
    base = np.full(n, A0)
    f0 = rhs(base, G, p)
    h = 1e-6
    e = base.copy(); e[0] += h
    col = (rhs(e, G, p) - f0) / h                    # circulant: one column gives the spectrum
    lam = np.fft.fft(col).real
    m = int(np.argmax(lam[1:n // 2]) + 1)
    unstable = np.where(lam[1:n // 2] > 0)[0] + 1
    band = (n / unstable.max(), n / unstable.min()) if len(unstable) else (float("nan"), float("nan"))
    return A0, lam[m], n / m, band


if __name__ == "__main__":
    p = dict(DEFAULT)
    print("baseline: A0=%.2f  lambda_max=%.3f  wavelength=%.1f cells  unstable band=%.1f-%.1f cells" % (
        (lambda r: (r[0], r[1], r[2], r[3][0], r[3][1]))(analyse(p))))
    for key, vals in (("D", [4, 5, 6, 7, 8, 9, 10, 12]), ("T", [22.5, 18, 15, 12, 10, 8]), ("b", [3, 2.5, 2.2, 2.0, 1.8, 1.6])):
        print(f"-- vary {key}")
        for v in vals:
            q = dict(p); q[key] = float(v)
            A0, lam, wl, band = analyse(q)
            print(f"   {key}={v:5}  lambda_max={lam:+7.3f}  wavelength={wl:5.1f}  band={band[0]:.1f}-{band[1]:.1f}")
    print("-- vary local auxin level at baseline parameters (depleted vs recovered tissue)")
    for a in (1, 2, 3, 4, 5, 6, 6.59, 8):
        A0, lam, wl, band = analyse(p, A_level=a)
        print(f"   A={a:5}  lambda_max={lam:+7.3f}  wavelength={wl:5.1f}  band={band[0]:.1f}-{band[1]:.1f}")
