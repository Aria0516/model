"""PROTOCOL revision 2: does the automatic crop give the same calibration quantities as the authors' crop on SAM7?

python validate_crop.py
"""
from pathlib import Path

from measure import measure

ROOT = Path(__file__).resolve().parents[2] / "reproductions" / "elife55832" / "outputs"
SEQ = "qDII-DR5-CLV3-LD_E27_170817_sam07"

A, B = ROOT / "validate_authors_crop" / SEQ, ROOT / "validate_auto_crop" / SEQ   # layout of the 2026-10-14 validation run
a, b = measure(A), measure(B)
ha = (A / "handedness.txt").read_text().splitlines()[0]
hb = (B / "handedness.txt").read_text().splitlines()[0]
checks = [
    ("d (um)", a["d"], b["d"], abs(b["d"] / a["d"] - 1) <= 0.03, "<= 3%"),
    ("CLV3 radius (um)", a["clv3_radius"], b["clv3_radius"], abs(b["clv3_radius"] - a["clv3_radius"]) <= 2, "<= 2 um"),
    ("P0 radius 0 h (um)", a["p0_radius_t00"], b["p0_radius_t00"],
     a["p0_radius_t00"] is not None and b["p0_radius_t00"] is not None and abs(b["p0_radius_t00"] - a["p0_radius_t00"]) <= 3, "<= 3 um"),
    ("P0 width 0 h (um)", a["p0_width_t00"], b["p0_width_t00"],
     a["p0_width_t00"] is not None and b["p0_width_t00"] is not None and abs(b["p0_width_t00"] / a["p0_width_t00"] - 1) <= 0.25, "<= 25%"),
]
for name, x, y, ok, crit in checks:
    print(f"{name:20s} authors {x if x is None else round(x, 2)}  auto {y if y is None else round(y, 2)}  ({crit}) {'pass' if ok else 'FAIL'}")
def final_orientation(line):
    """'score ... with orientation +1[; flipped to -1, ...]' -> the orientation the aligned files were written with."""
    if "flipped to" in line:
        return int(line.split("flipped to")[1].split(",")[0])
    return int(line.split("with orientation")[1].split(";")[0])


same_hand = final_orientation(ha) == final_orientation(hb)
print("handedness: authors:", ha, "| auto:", hb, "| same final orientation:", same_hand)
print("verdict:", "pass" if all(c[3] for c in checks) and same_hand else "FAIL")
