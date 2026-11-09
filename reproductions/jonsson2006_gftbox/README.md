# Jonsson 2006 in GFtbox 3D

This folder contains a GFtbox-style 3D embedding of the Jonsson et al. 2006 auxin-driven PIN transport model.

It reuses the Whitewoods et al. 2020 carnivorous-trap GFtbox 3D project as a mesh container, but replaces the interaction function with a Jonsson-style regulatory module.

## Paths

- GFtbox used: `C:\Users\xczhang\Desktop\modeling\code\GrowthToolbox-20190306-v6030\GrowthToolbox`
- Patched GFtbox project: `work\GPT_CarnivorousTraps_3D_20191031`
- Runner: `run_jonsson_gftbox_demo.m`
- Snapshot output: `outputs\jonsson_gftbox_t2.png`
- Exported arrays: `outputs\export`

## What Was Implemented

The GFtbox interaction function stores a custom state in `m.userdata.jonsson3d`:

- surface-node auxin concentration `A_i`
- internal PIN pool per surface node
- directed membrane PIN values `P_ij`
- a k-nearest-neighbor graph over surface nodes

Each GFtbox iteration runs the Jonsson-style update:

```math
\frac{dA_i}{dt}
=
D\sum_j(A_j-A_i)
+
T\sum_j(A_jP_{ji}-A_iP_{ij})
```

with explicit PIN cycling:

```math
\frac{dP_{ij}}{dt}=f(A_j)P_i-k_2P_{ij}
```

and Hill feedback:

```math
f(A)=k_1\frac{A^n}{K^n+A^n}
```

## GFtbox Morphogen Mapping

- `S_ADAXIAL`: normalized auxin field on surface nodes
- `ID_ADAXIAL`: top local auxin maxima, displayed as primordium candidates
- `S_ABAXIAL`: mean outgoing PIN occupancy
- `KPER`: increased near auxin maxima to create a small 3D bulging effect
- `KPAR`, `KPAR2`, `POL`, `POL2`: weak background growth/polarity fields for GFtbox rendering

## Run

From MATLAB:

```matlab
run('C:\Users\xczhang\Desktop\papers\reproductions\jonsson2006_gftbox\run_jonsson_gftbox_demo.m')
```

Headless command:

```powershell
& "C:\Users\xczhang\software\Matlab\bin\matlab.exe" -batch "run('C:\Users\xczhang\Desktop\papers\reproductions\jonsson2006_gftbox\run_jonsson_gftbox_demo.m')"
```

## Current Run

The verified run reached GFtbox time `t=2` and produced:

- surface nodes: `4971`
- displayed peak candidates: `12`
- auxin range: approximately `0.969` to `1.074`
- output image: `outputs\jonsson_gftbox_t2.png`

## Limitations

This is a GFtbox embedding/prototype, not an exact reproduction of Jonsson et al.'s original cell template:

- the GFtbox mesh is the Whitewoods 3D volumetric mesh, not an Arabidopsis SAM cell segmentation;
- the surface graph is constructed from nearest-neighbor surface nodes;
- displayed peaks are capped to the strongest local maxima for readability;
- growth mapping from auxin peaks to `KPER` is for visualization, not fitted to biological growth rates.

