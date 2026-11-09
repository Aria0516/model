# Python 3 compatibility patches to the authors' code (mounted over the image's copies; the snapshot in ../../sam_spaghetti is untouched)

Rule (noise_v3/PROTOCOL.md revision 4): only changes that leave the computation identical to what the code did under
Python 2; anything that would change an algorithm or a parameter is not patched but reported.

| # | file | line | change | why it is behaviour-preserving |
|---|---|---|---|---|
| 1 | sam_spaghetti/segmentation_quantification.py | 220 | `np.array(d.keys())` / `np.array(d.values())` → `np.array(list(d.keys()))` / `np.array(list(d.values()))` | under Python 2 `keys()`/`values()` were lists in matching order; under Python 3 they are views, which numpy wraps as a 0-d object array |
