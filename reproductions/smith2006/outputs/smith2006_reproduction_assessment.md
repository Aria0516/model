# Smith et al. 2006 Computational Figure Reproduction

## Scope

This package targets the computational figures in Smith et al. 2006:

- Fig.3: transport-based auxin/PIN pattern generation.
- Fig.4: simulated shoot apical meristem pattern classes and manipulations.
- Fig.5: divergence-angle transition from a decussate start toward the golden angle.

Experimental microscopy panels in Fig.1/Fig.2 are not simulated.

## Formula Coverage

The Fig.3 ring model uses the main-text mechanisms:

- PIN production increases with local IAA and decays.
- PIN allocation to the wall from cell i to neighbor j is proportional to `wall_length * b^IAA_j`.
- active auxin transport from i to j is proportional to local wall PIN and `IAA_i^2`, with saturation by `IAA_j`.
- IAA changes by production, decay, diffusion, active outflow, and active inflow.

## Reproduction Checks

- Fig.3 peak counts: `{'peaks_T3': 3, 'peaks_T4': 4, 'peaks_T10': 5}`.
- Fig.5 final model angle: `137.40` degrees.
- Fig.5 mean absolute model/measurement difference in this reconstructed curve: `1.71` degrees.

## Strictness Assessment

The reproduction is strict at the level of the main-text mechanism and panel structure, but not yet a bit-level recreation of the original VV simulation because the paper's Table 1 / Supporting Text parameter set is not present locally. Fig.4 and Fig.5 therefore use calibrated geometric/phenomenological rendering to match the paper's visual logic.

I attempted to download the PNAS supporting-information URLs for Table 1 / Supporting Text, but PNAS returned HTTP 403 from this environment.

To make this a stricter numerical reproduction, the next required input is the PNAS supporting information parameter table and, ideally, the original VV geometry/cell-division rules.
