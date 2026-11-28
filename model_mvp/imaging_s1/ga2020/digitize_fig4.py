"""Digitise GA2020 (eLife 55832) Fig 4G (Auxin = 1 - qDII) and 4H (DR5, 10^4 a.u.) box plots.

Source image: https://iiif.elifesciences.org/lax/55832%2Felife-55832-fig4-v1.tif/full/full/0/default.jpg (1379 x 1650 px).
Method: the plot frame (top/bottom horizontal lines, subplot separators) is located from dark rows/columns; the y axis is
calibrated linearly from the frame (G: 1.0 top, 0.6 bottom; H: 1.6 top, 0.0 bottom; checked against the tick marks);
for each box the central columns are averaged and the dark runs inside the coloured span give Q3 (top edge), median
(middle run) and Q1 (bottom edge). Values are run centroids, so the read-out error is about +-0.5 px
(G: +-0.0005 Auxin; H: +-0.002 x 10^4 DR5). Whisker ends are not read (they are not used).

python digitize_fig4.py <fig4.jpg>   ->  fig4GH_digitized.csv next to this script
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

HERE = Path(__file__).resolve().parent
img = np.asarray(Image.open(sys.argv[1]).convert("RGB")).astype(float)
gray = img.mean(2)
sat = img.max(2) - img.min(2)

PANELS = {  # x of left frame, separators, right frame; rows searched; axis range
    "G": dict(cols=[541, 616, 691, 766, 841, 917], xr=(500, 935), yr=(1150, 1650), lim=(0.6, 1.0), signal="Auxin (1 - qDII)"),
    "H": dict(cols=[1007, 1081, 1155, 1229, 1303, 1377], xr=(950, 1379), yr=(1150, 1650), lim=(0.0, 1.6), signal="DR5 (10^4 a.u.)"),
}
STAGES = [-3, -2, -1, 0, 1]
HOURS = [0, 5, 10]


def line_centroid(profile, lo, hi):
    """Centroid of darkness of the darkest line between lo and hi (inclusive)."""
    seg = profile[lo:hi + 1]
    i = int(np.argmin(seg))
    j0, j1 = max(i - 2, 0), min(i + 3, len(seg))
    w = np.clip(255 - seg[j0:j1], 0, None)
    return lo + float((w * np.arange(j0, j1)).sum() / w.sum())


rows = []
for name, p in PANELS.items():
    x0, x1 = p["xr"]; y0, y1 = p["yr"]
    sub = gray[1200:1590, x0:x1]
    colmean = sub.mean(0)
    # of the column mean that are much darker than the panel
    # vertical frame lines: approximate positions read off the image, refined to the darkest column within +-3 px
    vlines = [c - 3 + int(np.argmin(colmean[c - x0 - 3:c - x0 + 4])) for c in p["cols"]]
    rowmean = gray[y0:y1, vlines[0] + 3:vlines[-1] - 3].mean(1)
    top = line_centroid(rowmean, 0, 100) + y0
    bot = line_centroid(rowmean, len(rowmean) - 120, len(rowmean) - 1) + y0
    lo, hi = p["lim"]
    yval = lambda y: lo + (bot - y) / (bot - top) * (hi - lo)
    print(f"{name}: frame x {vlines}, top {top:.2f}, bottom {bot:.2f}, {(hi - lo) / (bot - top):.5f} units/px")
    assert len(vlines) == 6, vlines
    for si, st in enumerate(STAGES):
        a, b = vlines[si] + 2, vlines[si + 1] - 2
        s = sat[int(top) + 3:int(bot) - 3, a:b]
        colsat = (s > 60).sum(0)
        boxcols = np.where(colsat > 15)[0]
        runs = np.split(boxcols, np.where(np.diff(boxcols) > 1)[0] + 1)
        runs = [r for r in runs if len(r) >= 6]
        assert len(runs) == 3, (name, st, [len(r) for r in runs])
        for h, r in zip(HOURS, runs):
            c0, c1 = a + r[0], a + r[-1]
            mid = slice(c0 + len(r) // 4, c1 - len(r) // 4 + 1)
            colour = sat[int(top) + 3:int(bot) - 3, mid].mean(1) > 60
            ys = np.where(colour)[0] + int(top) + 3
            yt, yb = ys.min(), ys.max()
            prof = gray[:, mid].mean(1)
            q3 = line_centroid(prof, yt - 4, yt + 1)
            q1 = line_centroid(prof, yb - 1, yb + 4)
            med = line_centroid(prof, yt + 3, yb - 3)
            rows.append(dict(panel=name, signal=p["signal"], stage=st, hour=h,
                             q1=round(yval(q1), 4), median=round(yval(med), 4), q3=round(yval(q3), 4),
                             x_px=round((c0 + c1) / 2, 1), y_q3_px=round(q3, 2), y_med_px=round(med, 2), y_q1_px=round(q1, 2)))
D = pd.DataFrame(rows)
D.to_csv(HERE / "fig4GH_digitized.csv", index=False)
print(D.to_string(index=False))
