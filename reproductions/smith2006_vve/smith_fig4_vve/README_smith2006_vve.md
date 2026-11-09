# Smith et al. 2006 Fig.4 - VVe/Tissue 3D reconstruction

This folder is a VVe project for reconstructing the Smith et al. 2006 Fig.4 phyllotaxis panels in the original Algorithmic Botany VLab/L-studio + VVe environment.

## What is implemented

- VVe `Tissue` cell mesh using `cell`, `junction`, and `wall` objects.
- True 3D SAM dome geometry: UV coordinates are mapped to a 3D dome, and high-auxin/primordium-memory cells are lifted outward as organ protrusions.
- Cell-level auxin, PIN, primordium memory, and display value fields.
- Smith-style PIN allocation toward auxin-rich neighboring cells: `PIN_ij proportional to PIN_i * b^(auxin_j)`.
- Smith-style active auxin transport: `T * PIN_ij * auxin_i^2 / (1 + beta * auxin_j^2)`.
- Diffusion, auxin production/decay, auxin-dependent PIN up-regulation, and PIN decay.
- Fig.4 A-I scenario presets in `view.v` under `[Smith] Panel`.

## How to run

Build in VVe:

```bat
C:\Users\xczhang\Desktop\papers\reproductions\smith2006_vve\smith_fig4_vve\build_smith_fig4_vve.cmd
```

Open the interactive VVe model:

```bat
C:\Users\xczhang\Desktop\papers\reproductions\smith2006_vve\smith_fig4_vve\run_smith_fig4_vve.cmd
```

Change `view.v` -> `[Smith] Panel` from 1 to 9 for Fig.4 panels A-I, then rebuild/reload if needed.

## Outputs

3D preview sheet:

`C:\Users\xczhang\Desktop\papers\reproductions\smith2006_vve\outputs\smith_fig4_vve_3d_preview_sheet.png`

3D spiral rotation GIF:

`C:\Users\xczhang\Desktop\papers\reproductions\smith2006_vve\outputs\smith_fig4_vve_3d_spiral_rotation.gif`

2D top-view diagnostic sheet:

`C:\Users\xczhang\Desktop\papers\reproductions\smith2006_vve\outputs\smith_fig4_vve_cell_preview_sheet.png`

## Reproducibility boundary

This is a VVe/Tissue reimplementation, not the original Smith laboratory source. The original VV project and the full PNAS Supporting Information parameter table were not available locally, and PNAS supplement URLs tested during this work returned HTTP 403. The reconstruction is strict about the main-text equation structure, but the Fig.4 A-I panel fields are visually calibrated.
