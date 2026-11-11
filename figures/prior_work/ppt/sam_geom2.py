"""Geometry for the PowerPoint version of Fig. 1-2 A: an idealized shoot apex seen obliquely, wedge cut away.

Ray-casts the solid into a label map (top surface / primordium k / cut face 1-2 / floor), turns each region
into a smooth closed outline, and writes sam_shapes.json (slide inches, y down) for sam_a.js.
Shading is left to PowerPoint gradient fills, so the slide stays a handful of editable shapes.
Zone radii come from the main-line model (mech.npz); primordia are idealized along a 137.5 deg spiral.
    python sam_geom2.py mech.npz sam_shapes.json
"""
import json
import math
import sys

import contourpy
import numpy as np
from scipy import ndimage

par = json.loads(str(np.load(sys.argv[1])["par"]))
OUT = sys.argv[2]

R, W0, RC, RP = par["R_out"], par["w"], par["R_c"], par["R_p"]
RB = R + 1.0                                    # dome base radius (a little skirt beyond the tissue radius)
HD, T1, T2 = 10.0, 0.85, 1.7                     # dome height, L1 and inner-layer thickness (model units)
EL, AZ = math.radians(38), math.radians(-60)
WEDGE = math.radians(66)                        # narrow enough to leave P3 whole
SW, SH = 6.0, 5.7                               # slide (inches)
BOX = (1.2, 0.72, SW - 1.05, SH - 0.22)         # drawing area on the slide: x0, y0, x1, y1

th1 = AZ - WEDGE / 2 - math.radians(4)          # cut 1 passes through P1; view slightly towards cut 1
th2 = th1 + WEDGE
d1 = np.array([math.cos(th1), math.sin(th1)]); d2 = np.array([math.cos(th2), math.sin(th2)])
n1 = np.array([-d1[1], d1[0]]); n1 *= np.sign(n1 @ d2)
n2 = np.array([-d2[1], d2[0]]); n2 *= np.sign(n2 @ d1)

GA = math.radians(137.5)
prim = []
for k, r in [(1, 7.9), (2, 9.9), (3, 11.6), (4, 13.0)]:
    a = th1 - (k - 1) * GA
    prim.append(dict(k=k, c=np.array([r * math.cos(a), r * math.sin(a)]),
                     h=0.95 * W0 * (0.8 + 0.22 * k), a=W0 * (0.8 + 0.22 * k)))
P0 = 6.4 * np.array([math.cos(th1 + GA), math.sin(th1 + GA)])


def dome(x, y):
    return HD * np.clip(1.0 - (np.hypot(x, y) / RB) ** 2, 0, None) ** 0.85


def bumps(x, y):
    out = []
    for p in prim:
        s2 = ((x - p["c"][0]) ** 2 + (y - p["c"][1]) ** 2) / p["a"] ** 2
        out.append(p["h"] * np.clip(1.0 - s2, 0, None) ** (0.95 if p["k"] == 1 else 0.62))   # P1 is cut: softer
    return np.array(out)


def surf(x, y):
    return dome(x, y) + bumps(x, y).sum(0)


def in_wedge(x, y):
    return (x * n1[0] + y * n1[1] > 0) & (x * n2[0] + y * n2[1] > 0)


view = np.array([math.cos(EL) * math.cos(AZ), math.cos(EL) * math.sin(AZ), math.sin(EL)])   # towards the viewer
right = np.array([-math.sin(AZ), math.cos(AZ), 0.0])
up = np.cross(view, right)


def proj(P):
    P = np.atleast_2d(P)
    return np.c_[P @ right, P @ up]


# ---- ray-cast the label map
lim = RB + 3.0
corners = np.array([[x, y, z] for x in (-lim, lim) for y in (-lim, lim) for z in (0, HD + 5)])
cs = proj(corners)
NX = 1000
u0, u1 = cs[:, 0].min(), cs[:, 0].max(); v0, v1 = cs[:, 1].min(), cs[:, 1].max()
px = (u1 - u0) / NX
NY = int((v1 - v0) / px) + 1
U, V = np.meshgrid(u0 + px * (np.arange(NX) + 0.5), v1 - px * (np.arange(NY) + 0.5))
O = U.ravel()[:, None] * right + V.ravel()[:, None] * up + 45.0 * view    # ray origins, marching along -view
D = -view


def inside(P):
    x, y, z = P[:, 0], P[:, 1], P[:, 2]
    return (z > 0) & (z < surf(x, y)) & ~in_wedge(x, y)


N = len(O)
import hashlib, os
key = hashlib.md5(repr((R, RB, HD, EL, AZ, WEDGE, th1, [(p["c"].tolist(), p["h"], p["a"]) for p in prim], NX)).encode()).hexdigest()[:10]
cache = f"raycast_{key}.npz"
if os.path.exists(cache):
    _c = np.load(cache); t_hit, prev_t = _c["t_hit"], _c["prev_t"]
else:
    t_hit = None
if t_hit is None:
  t_hit = np.full(N, np.nan)
  active = np.arange(N)
  step, tmax = 0.12, 95.0
  t = np.zeros(N)
  prev_t = np.zeros(N)
  while active.size and t[active[0]] < tmax:
    P = O[active] + t[active, None] * D
    hit = inside(P)
    if hit.any():
        idx = active[hit]
        lo, hi = t[idx] - step, t[idx].copy()
        for _ in range(14):
            mid = 0.5 * (lo + hi)
            ins = inside(O[idx] + mid[:, None] * D)
            hi = np.where(ins, mid, hi); lo = np.where(ins, lo, mid)
        t_hit[idx] = hi
        prev_t[idx] = lo
        active = active[~hit]
    t[active] += step
  np.savez(cache, t_hit=t_hit, prev_t=prev_t)

lab = np.zeros(N, np.int8)            # 0 none, 1 floor, 2 top, 3 face 1, 4 face 2
hitm = ~np.isnan(t_hit)
Pin = O + np.nan_to_num(t_hit)[:, None] * D
Pout = O + prev_t[:, None] * D
top = hitm & (Pout[:, 2] >= surf(Pout[:, 0], Pout[:, 1]) - 1e-6)
wout = in_wedge(Pout[:, 0], Pout[:, 1])
f1 = hitm & ~top & wout & (Pout[:, :2] @ n1 > 0) & (Pin[:, :2] @ n1 <= 0)
f2 = hitm & ~top & ~f1 & wout
lab[top] = 2; lab[f1] = 3; lab[f2] = 4
# floor of the wedge: rays that miss the solid and land on z = 0 inside the wedge and the footprint
tz = O[:, 2] / view[2]
Q = O + tz[:, None] * D
floor = ~hitm & in_wedge(Q[:, 0], Q[:, 1]) & (np.hypot(Q[:, 0], Q[:, 1]) < RB)
lab[floor] = 1
depth = np.where(hitm, t_hit, np.inf)

# sub-labels
B = bumps(Pin[:, 0], Pin[:, 1])
part = np.where(top & (B.max(0) > 0.02), B.argmax(0) + 1, 0)       # primordium k on the top surface
below = surf(Pin[:, 0], Pin[:, 1]) - Pin[:, 2]                       # depth below the surface on a cut face
on_face = (lab == 3) | (lab == 4)
s_along = np.where(lab == 3, Pin[:, :2] @ d1, Pin[:, :2] @ d2)
sp = float(np.hypot(*prim[0]["c"]))
strand = (lab == 3) & (np.abs(s_along - sp) < 0.95) & (below > T1 + T2)
img = lambda m: m.reshape(NY, NX)


def to_slide_factory():
    allpts = np.argwhere(img(lab > 0))
    r0, c0 = allpts.min(0); r1, c1 = allpts.max(0)
    sc = min((BOX[2] - BOX[0]) / (c1 - c0), (BOX[3] - BOX[1]) / (r1 - r0))
    ox = BOX[0] + ((BOX[2] - BOX[0]) - sc * (c1 - c0)) / 2 - sc * c0
    oy = BOX[1] + ((BOX[3] - BOX[1]) - sc * (r1 - r0)) / 2 - sc * r0
    pix = lambda rc: np.c_[ox + sc * rc[:, 1], oy + sc * rc[:, 0]]            # (row, col) -> inches
    world = lambda P: pix(np.c_[(v1 - proj(P)[:, 1]) / px - 0.5, (proj(P)[:, 0] - u0) / px - 0.5])
    return pix, world, sc


pix, world, SC = to_slide_factory()


def rdp(P, eps):
    if len(P) < 3:
        return P
    a, b = P[0], P[-1]
    ab = b - a; n = np.hypot(*ab)
    d = np.abs(ab[0] * (P[:, 1] - a[1]) - ab[1] * (P[:, 0] - a[0])) / n if n > 0 else np.hypot(*(P - a).T)
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.vstack([rdp(P[: i + 1], eps)[:-1], rdp(P[i:], eps)])
    return np.vstack([a, b])


def outlines(mask, grow=0.0, min_area=40, sigma=1.1):
    m = mask.astype(float)
    if grow > 0:
        m = ndimage.binary_dilation(mask, iterations=int(grow)).astype(float)
    m = ndimage.gaussian_filter(m, sigma)
    m = np.pad(m, 1)
    out = []
    for L in contourpy.contour_generator(z=m).lines(0.5):
        if len(L) < 8:
            continue
        x, y = L[:, 0] - 1, L[:, 1] - 1
        area = 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        if area < min_area:
            continue
        rc = rdp(np.c_[y, x], 0.35)
        out.append(pix(rc))
    return out


shapes = []


def add_poly(name, polys, fill, grad=None, line=None, lw=0.0, transparency=0):
    for i, P in enumerate(polys):
        shapes.append(dict(kind="poly", name=f"{name}" + (f"_{i}" if len(polys) > 1 else ""),
                           pts=np.round(P, 4).tolist(), fill=fill, grad=grad, line=line, lw=lw,
                           transparency=transparency))


def add_line(name, P, color, lw, dash=None, arrow=False):
    shapes.append(dict(kind="line", name=name, pts=np.round(np.asarray(P), 4).tolist(), color=color, lw=lw,
                       dash=dash, arrow=arrow))


def visible(P, tol=0.25):
    """3D point visible: the ray through its pixel hits it (and not something nearer)."""
    P = np.atleast_2d(P)
    q = proj(P)
    c = np.clip(((q[:, 0] - u0) / px).astype(int), 0, NX - 1)
    r = np.clip(((v1 - q[:, 1]) / px).astype(int), 0, NY - 1)
    t_pt = (O[r * NX + c] - P) @ view                     # distance along the ray from its origin
    return np.abs(depth[r * NX + c] - t_pt) < tol


# ---- shadow (soft, under the dome)
th = np.linspace(0, 2 * np.pi, 145)
S = np.c_[1.05 * RB * np.cos(th) + 0.6, 1.05 * RB * np.sin(th) - 0.6, np.zeros_like(th)]
add_poly("shadow", [world(S)], "DCDCDC",
         grad=dict(type="path", focus=[50, 50], stops=[[0, "CFCFCF", 0], [75, "DCDCDC", 0], [100, "F7F7F7", 0]]))

# ---- floor of the cut
add_poly("cut_floor", outlines(img(lab == 1), grow=1), "E4E4E4", line="C8C8C8", lw=0.5)

# ---- dome (whole visible top surface), shaded by a radial gradient lit from the upper left
dome_focus = [44, 30]
add_poly("dome", outlines(img(lab == 2), grow=1), "2A9D8F", line="27466B", lw=0.75,
         grad=dict(type="path", focus=dome_focus,
                   stops=[[0, "8BD47A", 0], [30, "4DBA80", 0], [62, "26918B", 0], [88, "2E6B8E", 0], [100, "38497E", 0]]))

# ---- incipient site P0: soft yellow spot
e = np.c_[P0[0] + 2.0 * np.cos(th), P0[1] + 2.0 * np.sin(th)]
add_poly("incipient_P0", [world(np.c_[e, surf(e[:, 0], e[:, 1])])], "FDE725",
         grad=dict(type="path", focus=[50, 50], stops=[[0, "FDE725", 0], [45, "E8E43A", 15], [100, "C8DF45", 100]]))

# ---- primordia, older first; colours from young (auxin-rich, yellow) to old (green)
PG = {1: ["FDE725", "C9E03E", "6CBF63", "2E8C6E"], 2: ["E6E63C", "A6D94E", "4FAE73", "2A7E73"],
      3: ["CDE24A", "86CF5B", "3B9F7E", "286F78"], 4: ["B4DC50", "66C468", "2F8F84", "27607A"]}
for p in sorted(prim, key=lambda p: -p["k"]):
    m = img(part == p["k"])
    if m.sum() < 30:
        continue
    g = PG[p["k"]]
    add_poly(f"primordium_P{p['k']}", outlines(m), g[1], line="2F6B5E", lw=0.6,
             grad=dict(type="path", focus=[36, 26], stops=[[0, g[0], 0], [40, g[1], 0], [80, g[2], 0], [100, g[3], 0]]))

# ---- light and shade: Lambert shading of the top surface, drawn as stacked translucent shapes
ex = 1e-3
Sx = (surf(Pin[:, 0] + ex, Pin[:, 1]) - surf(Pin[:, 0] - ex, Pin[:, 1])) / (2 * ex)
Sy = (surf(Pin[:, 0], Pin[:, 1] + ex) - surf(Pin[:, 0], Pin[:, 1] - ex)) / (2 * ex)
nrm = np.c_[-Sx, -Sy, np.ones(N)]; nrm /= np.linalg.norm(nrm, axis=1)[:, None]
Lt = -0.55 * right + 0.55 * up + 0.65 * view; Lt /= np.linalg.norm(Lt)
lam = np.where(lab == 2, nrm @ Lt, 1.0)
for i, c in enumerate(np.linspace(0.72, 0.12, 12)):
    add_poly(f"shade_{i}", outlines(img((lab == 2) & (lam < c)), sigma=2.6, min_area=25), "0B2545", transparency=94)
on_prim = img(part > 0)
for i, c in enumerate((0.95, 0.985)):          # small glints on the primordia only
    add_poly(f"highlight_{i}", outlines(img((lab == 2) & (lam > c)) & on_prim, sigma=1.4, min_area=12), "FFFFFF",
             transparency=72)

# ---- competent ring: two dashed circles, visible arcs only
for r in (RC, RP):
    tt = np.linspace(0, 2 * np.pi, 721)
    X, Y = r * np.cos(tt), r * np.sin(tt)
    P = np.c_[X, Y, surf(X, Y) + 0.02]
    ok = visible(P, 0.35) & ~in_wedge(X, Y) & (bumps(X, Y).max(0) < 0.05)     # passes behind primordia
    runs, cur = [], []
    for i in range(len(tt)):
        if ok[i]:
            cur.append(i)
        else:
            if len(cur) > 6: runs.append(cur)
            cur = []
    if len(cur) > 6:
        if runs and runs[0][0] == 0: runs[0] = cur + runs[0]
        else: runs.append(cur)
    for j, run in enumerate(runs):
        add_line(f"competent_ring_{r:g}_{j}", world(P[run]), "C0392B", 1.7, dash="dash")

# ---- PIN1 polarity arrows: towards the summit, and towards P0 near it
rng = np.random.default_rng(7)
n_arrows = 0
cand = []
for _ in range(3000):
    r = RB * math.sqrt(rng.uniform(0.03, 0.62)); a = rng.uniform(0, 2 * math.pi)
    cand.append((r * math.cos(a), r * math.sin(a)))
placed = []
for x, y in cand:
    if in_wedge(x + 2.2 * (n1[0] + n2[0]) / 2, y + 2.2 * (n1[1] + n2[1]) / 2) or in_wedge(x, y):
        continue
    if any(math.hypot(x - p["c"][0], y - p["c"][1]) < 1.25 * p["a"] for p in prim):
        continue
    if math.hypot(x - P0[0], y - P0[1]) < 2.3 or any(math.hypot(x - a, y - b) < 2.6 for a, b in placed):
        continue
    near = math.hypot(x - P0[0], y - P0[1]) < 6.0
    tgt = P0 if near else np.zeros(2)
    d = tgt - np.array([x, y]); n = np.hypot(*d)
    if n < 1.2:
        continue
    d = 1.45 * d / n
    P = np.array([[x, y, float(surf(x, y)) + 0.05], [x + d[0], y + d[1], float(surf(x + d[0], y + d[1])) + 0.05]])
    if visible(P, 0.35).all():
        add_line(f"pin1_arrow_{len(placed)}", world(P), "FFFFFF", 1.4, arrow=True)
        placed.append((x, y))
    if len(placed) >= 26:
        break

# ---- cut faces: whole face (deep tissue, vertical gradient), inner layer, L1, vascular strand
for f, tag in ((3, "cut1"), (4, "cut2")):
    m = img(lab == f)
    add_poly(f"{tag}_face", outlines(m, grow=1), "EDE7DC", line="3A3A3A", lw=0.6,
             grad=dict(type="lin", ang=90, stops=[[0, "F8F5EF", 0], [100, "D9CFBE", 0]]))
    add_poly(f"{tag}_inner_layer", outlines(m & img(below < T1 + T2), sigma=0.9, min_area=15), "BDBDBD",
             line="7A7A7A", lw=0.4)
    add_poly(f"{tag}_L1", outlines(m & img(below < T1), sigma=0.8, min_area=10), "43A96E", line="2E6B4C", lw=0.4)
add_poly("vascular_strand", outlines(img(strand), sigma=0.9), "8F8F8F", line="3A3A3A", lw=0.6,
         grad=dict(type="lin", ang=0, stops=[[0, "7A7A7A", 0], [50, "A6A6A6", 0], [100, "7A7A7A", 0]]))

# top edges of the cut faces and the wedge axis
for d, tag in ((d1, "cut1"), (d2, "cut2")):
    s = np.linspace(0, RB, 400)
    P = np.c_[s * d[0], s * d[1], surf(s * d[0], s * d[1])]
    P = P[P[:, 2] > 0.01]
    add_line(f"{tag}_edge", world(P), "1A1A1A", 1.5)
add_line("wedge_axis", world(np.array([[0, 0, float(surf(0, 0))], [0, 0, 0]])), "3A3A3A", 0.8)

# drainage: dashed arrow from L1 into the strand, and a white arrow down the strand
zt = float(surf(*(sp * d1)))
c3 = lambda z: np.array([[sp * d1[0], sp * d1[1], z]])
add_line("drainage_arrow", world(np.r_[c3(zt - 0.3), c3(zt - T1 - T2 + 0.1)]), "1A1A1A", 1.4, dash="dash", arrow=True)
add_line("strand_arrow", world(np.r_[c3(0.7 * (zt - T1 - T2)), c3(0.25 * (zt - T1 - T2))]), "FFFFFF", 1.8, arrow=True)

# ---- label anchors
ring_r = 0.5 * (RC + RP)
cands = []
for a in np.linspace(0, 2 * np.pi, 360, endpoint=False):
    X, Y = ring_r * math.cos(a), ring_r * math.sin(a)
    P = np.array([[X, Y, float(surf(X, Y))]])
    if not in_wedge(X, Y) and visible(P, 0.35)[0]:
        cands.append(P)
ring_l = min(cands, key=lambda P: world(P)[0, 0])
p_vis = [p for p in prim[1:] if (img(part == p["k"])).sum() > 200]
p_r = max(p_vis, key=lambda p: world(np.r_[p["c"], surf(*p["c"])][None])[0, 0])
q_r = p_r["c"]
anchors = {
    "cz": world(np.array([[0, 0, float(surf(0, 0))]]))[0],
    "ring": world(ring_l)[0],
    "prim": world(np.array([[q_r[0], q_r[1], float(surf(*q_r))]]))[0],
    "L1": world(np.array([[*(0.86 * RB * d1), float(surf(*(0.86 * RB * d1))) - T1 / 2]]))[0],
    "inner": world(np.array([[*(0.22 * RB * d1), float(surf(*(0.22 * RB * d1))) - T1 - T2 / 2]]))[0],
    "strand": world(np.r_[c3(0.45 * (zt - T1 - T2))])[0],
}
json.dump(dict(slide=[SW, SH], shapes=shapes, anchors={k: np.round(v, 4).tolist() for k, v in anchors.items()}),
          open(OUT, "w"))
print(f"grid {NX}x{NY} | shapes {len(shapes)} | arrows {len(placed)} | pts "
      f"{sum(len(s['pts']) for s in shapes)}")
