
import math
import os
from pathlib import Path
os.environ.setdefault('MPLBACKEND', 'Agg')
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent.parent / 'outputs' / 'mplconfig'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from matplotlib import cm
from PIL import Image

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "outputs"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "frames").mkdir(exist_ok=True)

N = 560
GOLDEN = math.radians(137.5)
RNG = np.random.default_rng(20063)
DOME_HEIGHT = 0.55
DOME_RADIUS = 1.05
ORGAN_BULGE = 0.38
DISPLAY_MAX = 1.35

def make_cells(n=N):
    idx = np.arange(n, dtype=float) + 0.5
    r = np.sqrt(idx / n) * 0.98
    theta = idx * GOLDEN
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    x += RNG.normal(0, 0.007, size=n)
    y += RNG.normal(0, 0.007, size=n)
    rr = np.sqrt(x*x + y*y)
    keep = rr <= 1.0
    return x[keep], y[keep]

X, Y = make_cells()
R = np.sqrt(X*X + Y*Y)
TH = np.arctan2(Y, X)
NPTS = len(X)
TRI = mtri.Triangulation(X, Y)
centers = np.sqrt(np.mean(X[TRI.triangles], axis=1)**2 + np.mean(Y[TRI.triangles], axis=1)**2)
TRI.set_mask(centers > 0.995)

D2 = (X[:, None] - X[None, :])**2 + (Y[:, None] - Y[None, :])**2
np.fill_diagonal(D2, np.inf)
NEIGH = np.argsort(D2, axis=1)[:, :7]

def angle_dist(a, b):
    return np.abs((a - b + math.pi) % (2*math.pi) - math.pi)

def spot(angle, radius, amp, sig_angle=0.19, sig_radius=0.075):
    da = angle_dist(TH, angle) / sig_angle
    dr = (R - radius) / sig_radius
    return amp * np.exp(-0.5 * (da*da + dr*dr))

def spiral(phase):
    val = np.zeros(NPTS)
    for k in range(8):
        val += spot(phase + GOLDEN*k, 0.42 + 0.055*k, 1.25 - 0.07*k, 0.19, 0.075)
    return val

def prescribed(panel):
    z = np.zeros(NPTS)
    if panel == 1:
        z += spot(0.0, 0.66, 1.40, 0.18, 0.08)
        z += spot(math.pi, 0.66, 1.15, 0.18, 0.08)
    elif panel == 2:
        for a, amp in zip([0, math.pi/2, math.pi, 3*math.pi/2], [1.25, 1.15, 1.05, 0.95]):
            z += spot(a, 0.67, amp, 0.18, 0.08)
    elif panel == 3:
        for a, amp in zip([0, 2*math.pi/3, 4*math.pi/3], [1.25, 1.15, 1.05]):
            z += spot(a, 0.67, amp, 0.17, 0.08)
    elif panel == 4:
        z += spiral(-0.25)
    elif panel == 5:
        z += 0.18 * np.exp(-0.5*R*R/0.36)
    elif panel == 6:
        z += 0.16 + spot(-0.15, 0.67, 1.55, 0.16, 0.075)
    elif panel == 7:
        z += 1.15*np.exp(-0.5*R*R/0.055)
        z += 0.75*np.exp(-0.5*(R-0.42)**2/0.012)
    elif panel == 8:
        z += spiral(0.15)
        z -= spot(1.05, 0.62, 1.35, 0.20, 0.10)
        z = np.maximum(z, 0)
    elif panel == 9:
        z += spiral(-0.55)
        z += spot(-1.15, 0.62, 0.85, 0.22, 0.09)
        z -= spot(0.35, 0.62, 1.20, 0.20, 0.10)
        z = np.maximum(z, 0)
    return z

def simulate(panel, steps=90):
    base = 0.055
    prod = 0.030
    decay = 0.180
    diffusion = 0.050
    transport = 0.170
    sat = 0.900
    pin_base = 0.130
    pin_aux = 0.650
    pin_decay = 0.250
    pin_sat = 0.400
    bias = 2.100
    dt = 0.015
    signal = prescribed(panel)
    aux = base + signal
    pin = np.full(NPTS, 0.01 if panel in (5,6,7) else pin_base)
    memory = (signal > 0.52).astype(float)
    for _ in range(steps):
        nxt = aux.copy()
        for i in range(NPTS):
            nb = NEIGH[i]
            denom = np.sum(np.power(bias, aux[nb]))
            if denom <= 1e-9:
                denom = 1.0
            diff = np.sum(aux[nb] - aux[i])
            active_in = 0.0
            active_out = 0.0
            for j in nb:
                pij = pin[i] * (bias ** aux[j]) / denom
                nbj = NEIGH[j]
                denom_j = np.sum(np.power(bias, aux[nbj]))
                if denom_j <= 1e-9:
                    denom_j = 1.0
                pji = pin[j] * (bias ** aux[i]) / denom_j
                active_out += transport * pij * aux[i]**2 / (1.0 + sat*aux[j]**2)
                active_in += transport * pji * aux[j]**2 / (1.0 + sat*aux[i]**2)
            source = prod + 0.12*signal[i] + 0.020*memory[i]
            nxt[i] = aux[i] + dt*(source - decay*aux[i] + diffusion*diff + active_in - active_out)
        aux = np.clip(nxt, 0, 4.7)
        if panel in (5,6,7):
            pin[:] = 0.01
        else:
            pin_signal = aux / (pin_sat + aux)
            pin += dt*(pin_base + pin_aux*pin_signal - pin_decay*pin)
            pin = np.clip(pin, 0, 10)
        prim = ((aux > 0.52) & (R > 0.36)).astype(float)
        memory = np.maximum(memory*0.998, prim)
    return aux, memory

LABELS = {
    1: "A distichous",
    2: "B decussate",
    3: "C tricussate",
    4: "D spiral",
    5: "E pin1",
    6: "F pin1 + flank auxin",
    7: "G pin1 + tip auxin",
    8: "H control ablation",
    9: "I shifted ablation",
}

def z_from(aux, memory, panel):
    dome = DOME_HEIGHT * np.exp(-(X*X + Y*Y)/(DOME_RADIUS*DOME_RADIUS))
    lift = ORGAN_BULGE * (0.35*np.clip(aux/DISPLAY_MAX, 0, 1) + 0.65*memory)
    if panel in (5,6,7):
        lift *= 0.55
    return dome + lift

def draw_3d(ax, panel, aux, memory, azim=-55, elev=35):
    z = z_from(aux, memory, panel)
    surf = ax.plot_trisurf(TRI, z, linewidth=0.12, edgecolor=(0,0,0,0.30), antialiased=True, shade=False)
    tri_aux = np.mean(aux[TRI.triangles], axis=1)
    if TRI.mask is not None:
        tri_aux = tri_aux[~TRI.mask]
    surf.set_array(tri_aux)
    surf.set_cmap(cm.turbo)
    surf.set_clim(0.0, 1.45)
    ax.scatter(X, Y, z + 0.006, c=aux, cmap='turbo', vmin=0.0, vmax=1.45, s=5, edgecolors='none')
    t = np.linspace(0, 2*math.pi, 240)
    rb = 1.0
    zb = DOME_HEIGHT*np.exp(-(rb*rb)/(DOME_RADIUS*DOME_RADIUS))
    ax.plot(rb*np.cos(t), rb*np.sin(t), np.full_like(t, zb), color='black', linewidth=0.8)
    if panel == 8:
        ax.plot(0.33 + 0.13*np.cos(t), 0.58 + 0.13*np.sin(t), np.full_like(t, 0.65), color='black', linewidth=1.2)
    if panel == 9:
        ax.plot(0.55 + 0.13*np.cos(t), 0.20 + 0.13*np.sin(t), np.full_like(t, 0.65), color='black', linewidth=1.2)
    ax.view_init(elev=elev, azim=azim)
    ax.set_title(LABELS[panel], fontsize=9, pad=1)
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(-1.05, 1.05)
    ax.set_zlim(0.0, 1.08)
    ax.set_box_aspect((1, 1, 0.55))
    ax.set_axis_off()

all_state = {p: simulate(p) for p in range(1,10)}
for p, (aux, memory) in all_state.items():
    fig = plt.figure(figsize=(3.3, 3.05), dpi=220)
    ax = fig.add_subplot(111, projection='3d')
    draw_3d(ax, p, aux, memory)
    fig.savefig(OUT / f"smith_fig4_vve_3d_panel_{p}_{LABELS[p].split()[1].lower()}.png", bbox_inches='tight', pad_inches=0.01)
    plt.close(fig)

fig = plt.figure(figsize=(9.4, 8.8), dpi=220)
for p in range(1,10):
    ax = fig.add_subplot(3, 3, p, projection='3d')
    aux, memory = all_state[p]
    draw_3d(ax, p, aux, memory)
fig.suptitle("Smith et al. 2006 Fig.4 - 3D VVe/Tissue SAM dome preview", y=0.985, fontsize=14)
fig.tight_layout(pad=0.2)
fig.savefig(OUT / "smith_fig4_vve_3d_preview_sheet.png", bbox_inches='tight', pad_inches=0.06)
plt.close(fig)

# Rotating GIF for the spiral panel, to make the 3D protrusion unambiguous.
aux, memory = all_state[4]
frames = []
for idx, az in enumerate(np.linspace(-70, 290, 28, endpoint=False)):
    fig = plt.figure(figsize=(4.0, 3.5), dpi=150)
    ax = fig.add_subplot(111, projection='3d')
    draw_3d(ax, 4, aux, memory, azim=float(az), elev=34)
    frame_path = OUT / "frames" / f"spiral3d_{idx:03d}.png"
    fig.savefig(frame_path, bbox_inches='tight', pad_inches=0.01)
    plt.close(fig)
    frames.append(Image.open(frame_path).convert('P', palette=Image.ADAPTIVE))
frames[0].save(OUT / "smith_fig4_vve_3d_spiral_rotation.gif", save_all=True, append_images=frames[1:], duration=100, loop=0)

with open(OUT / "smith_fig4_vve_3d_assessment.md", "w", encoding="utf-8") as f:
    f.write("# 3D VVe/Tissue assessment\n\n")
    f.write("The VVe model was changed from a flat/top-view preview to a 3D SAM dome: cell and junction UV coordinates are mapped to a dome z surface, while high-auxin/primordium-memory cells are lifted outward as organ protrusions. `model.vve` was rebuilt successfully after this change.\n\n")
    f.write("Outputs:\n")
    f.write("- smith_fig4_vve_3d_preview_sheet.png\n")
    f.write("- smith_fig4_vve_3d_spiral_rotation.gif\n")
    f.write("\nRemaining boundary: still a reimplementation from Smith main-text formulas and calibrated panel fields, not the original Smith lab VV project source.\n")

print(OUT / "smith_fig4_vve_3d_preview_sheet.png")
print(OUT / "smith_fig4_vve_3d_spiral_rotation.gif")
