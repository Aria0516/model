# Jonsson 2006 GFtbox Biomorphic Simulation

This run upgrades the earlier surface-field visualization into a persistent-primordia growth simulation.

## Implemented changes

- Kept the Jonsson auxin/PIN ODE as the signaling core.
- Added primordium identity memory: high auxin local maxima are registered as persistent primordia when they exceed threshold and are far enough from existing primordia.
- Converted persistent primordia into an organ field that continues to drive growth after the initiating auxin peak changes.
- Increased GFtbox growth rates to the same order as the Whitewoods carnivorous-trap model:
  - pre-growth phase before t=1 uses near-zero growth;
  - after t=1, organ field drives stronger KPER and KPAR growth.
- Extended the output to 8 time points from t=0.5 to t=12.

## Quantitative result

From `biomorphic_summary.csv`:

- primordia count: 0 at t=0.5, 1 at t=1, 2 at t=2, 4 at t=4, 6 from t=6 onward.
- max displacement: 0.0033 at t=0.5 to 1.7440 at t=12.
- mean displacement: 0.0013 at t=0.5 to 0.5533 at t=12.
- KPER max: 0.002 before growth to about 0.314 after primordium-driven growth begins.
- auxin contrast: 0.0325 at t=0.5 to 0.3290 at t=12.

## Output files

- `jonsson_biomorphic_timeseries_sheet.png`: 8-panel stage sheet.
- `jonsson_biomorphic_timeseries.gif`: animated sequence.
- `jonsson_biomorphic_frame_differences.png`: amplified frame-to-frame difference map.
- `jonsson_biomorphic_assessment.svg`: dynamic assessment plot.
- `export/`: per-time-point surface auxin/PIN/primordium/organ-field data plus final mesh exports.

## Assessment

The three requested shortcomings are addressed at the implementation level:

- 3D outgrowth is no longer weak: the final mesh has large measured displacement and KPER is in the biological-shape-model range used by the source GFtbox model.
- Primordia now have identity memory: once initiated, they remain as a persistent field and keep driving local growth.
- The sequence is no longer a single static field snapshot: it runs through t=12 and exports 8 visual stages plus a GIF.

Scientific boundary: this is still a qualitative GFtbox morphodynamic reconstruction on the Whitewoods mesh, not a validated Arabidopsis SAM cell-resolved model. It is suitable for visual/mechanistic demonstration, not for claiming quantitative biological prediction.
