# Smith et al. 2006 Fig.4 - MATLAB + GFtbox 3D reconstruction

## What was built

- GFtbox `leaf_hemisphere` creates the common SAM dome mesh.
- The nine Smith Fig.4 panels A-I are derived from that common 3D dome.
- Primordia are represented as persistent auxin-high Gaussian outgrowths on the peripheral zone.
- pin1, local side auxin, tip auxin ring, control, and ablation panels are rendered as separate model states.

## Mesh

- base nodes: 910
- base triangles: 1722

## Strictness

This is a 3D GFtbox-style reconstruction of Smith Fig.4 morphology and panel logic, not an exact VV numerical rerun. The paper states that the original Fig.4 parameter values were in PNAS Supporting Information Table 1; those URLs returned HTTP 403 from this environment.

The strongest matches are Fig.4 A-D pattern classes and F/G manipulation outcomes. The weakest strict-match aspect is cell-level geometry: this version uses a GFtbox triangular dome mesh instead of the original VV cell complex and division rules.
