import math
import os
from pathlib import Path
os.environ.setdefault('MPLBACKEND', 'Agg')
os.environ.setdefault('MPLCONFIGDIR', str(Path(__file__).resolve().parent.parent / 'outputs' / 'mplconfig'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "outputs"
OUT.mkdir(parents=True, exist_ok=True)

N = 520
GOLDEN = math.radians(137.5)
RNG = np.random.default_rng(2006)

def make_cells(n=N):
    idx = np.arange(n, dtype=float) + 0.5
    r = np.sqrt(idx / n) * 0.98
    theta = idx * GOLDEN
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    x += RNG.normal(0, 0.010, size=n)
    y += RNG.normal(0, 0.010, size=n)
    rr = np.sqrt(x*x + y*y)
    keep = rr <= 1.0
    return x[keep], y[keep]

X, Y = make_cells()
R = np.sqrt(X*X + Y*Y)
TH = np.arctan2(Y, X)
NPTS = len(X)

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

def simulate(panel, steps=85):
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
    return aux

LABELS = {
    1: "A  distichous",
    2: "B  decussate",
    3: "C  tricussate",
    4: "D  spiral",
    5: "E  pin1",
    6: "F  pin1 + flank auxin",
    7: "G  pin1 + tip auxin",
    8: "H  control ablation",
    9: "I  shifted ablation",
}

def draw_panel(ax, panel, aux):
    ax.scatter(X, Y, c=aux, s=66, marker='h', cmap='turbo', vmin=0.0, vmax=1.45,
               edgecolors=(0.05,0.05,0.05,0.78), linewidths=0.22)
    ax.add_patch(plt.Circle((0,0), 1.01, fill=False, color='black', linewidth=1.1))
    if panel == 8:
        ax.add_patch(plt.Circle((0.33, 0.58), 0.13, fill=False, color='white', linewidth=2.1))
        ax.add_patch(plt.Circle((0.33, 0.58), 0.13, fill=False, color='black', linewidth=0.9))
    if panel == 9:
        ax.add_patch(plt.Circle((0.55, 0.20), 0.13, fill=False, color='white', linewidth=2.1))
        ax.add_patch(plt.Circle((0.55, 0.20), 0.13, fill=False, color='black', linewidth=0.9))
    ax.set_title(LABELS[panel], fontsize=10, pad=3)
    ax.set_aspect('equal')
    ax.set_xlim(-1.04, 1.04)
    ax.set_ylim(-1.04, 1.04)
    ax.axis('off')

all_aux = {p: simulate(p) for p in range(1,10)}
for p, aux in all_aux.items():
    fig, ax = plt.subplots(figsize=(3.0, 3.0), dpi=220)
    draw_panel(ax, p, aux)
    fig.savefig(OUT / f"smith_fig4_vve_panel_{p}_{LABELS[p].split()[1].lower()}.png", bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)

fig, axes = plt.subplots(3, 3, figsize=(9.2, 9.2), dpi=220)
for ax, p in zip(axes.flat, range(1,10)):
    draw_panel(ax, p, all_aux[p])
fig.suptitle("Smith et al. 2006 Fig.4 - VVe/Tissue model preview", y=0.995, fontsize=14)
fig.tight_layout(pad=0.55)
fig.savefig(OUT / "smith_fig4_vve_cell_preview_sheet.png", bbox_inches='tight', pad_inches=0.08)
plt.close(fig)

stats = []
for p, aux in all_aux.items():
    thresh = max(0.52, float(np.quantile(aux, 0.985)))
    peaks = int(np.sum(aux > thresh))
    stats.append((p, float(aux.min()), float(aux.max()), float(aux.mean()), peaks))

with open(OUT / "smith_fig4_vve_preview_assessment.md", "w", encoding="utf-8") as f:
    f.write("# Smith 2006 Fig.4 VVe preview assessment\n\n")
    f.write("This sheet is a batch-rendered preview using the same panel fields and Smith-style auxin/PIN transport terms embedded in the VVe `model.vvl`. The authoritative interactive model is `smith_fig4_vve/model.vve`; this preview exists because VVe does not expose a stable headless PNG exporter.\n\n")
    f.write("## Panel statistics\n\n")
    f.write("panel,min_auxin,max_auxin,mean_auxin,high_auxin_cells\n")
    for row in stats:
        f.write(f"{row[0]},{row[1]:.4f},{row[2]:.4f},{row[3]:.4f},{row[4]}\n")
    f.write("\n## Fit judgement\n\n")
    f.write("Better than the earlier GFtbox surface for Smith Fig.4 because it is cell-level, has explicit PIN/auxin states, and separates pin1/local auxin/ablation panels. It is still not an exact original-parameter reproduction because the Smith supplementary parameter table and original VV project source were not available locally or through accessible PNAS supplement URLs.\n")

print(OUT / "smith_fig4_vve_cell_preview_sheet.png")


