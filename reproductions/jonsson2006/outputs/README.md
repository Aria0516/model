# Jonsson et al. 2006 minimal reproduction

This run implements the one-dimensional periodic simplified model around Eq. 1.

Parameters:

- cells: `50`
- time step: `0.02`
- steps: `20000`
- transport `T`: `1.0`
- total membrane PIN `P`: `1.0`
- seed: `3`
- initial noise amplitude: `0.001`

| case | D/(TP) | final peak count | final std | final min | final max |
|---|---:|---:|---:|---:|---:|
| pattern-forming | 0.100 | 6 | 1.2548 | 0.0014 | 4.9588 |
| uniform-stable | 0.550 | 0 | 0.0001 | 0.9999 | 1.0002 |

Interpretation: when active transport feedback dominates diffusion, the near-uniform auxin state breaks into a peak-trough pattern. When diffusion is too strong, the uniform state remains stable.
