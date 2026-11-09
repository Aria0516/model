import sys
import numpy as np
from tissue_nukem_3d.microscopy_images import tifffile
from tissue_nukem_3d.microscopy_images.read_microscopy_image import read_czi_image
CH = ['DIIV', 'DR5', 'TagBFP', 'CLV3']
img = read_czi_image(sys.argv[1], channel_names=CH)
a = {c: np.asarray(img[c].get_array() if hasattr(img[c], 'get_array') else img[c]) for c in CH}
raw = tifffile.imread(sys.argv[2])
mask = (raw > 0).any(axis=1)
for name, f in [('zyx', lambda v: np.transpose(v, (2, 1, 0))), ('zxy', lambda v: np.transpose(v, (2, 0, 1))),
                ('zyx flip y', lambda v: np.transpose(v, (2, 1, 0))[:, ::-1, :]), ('zyx flip x', lambda v: np.transpose(v, (2, 1, 0))[:, :, ::-1]),
                ('zyx flip z', lambda v: np.transpose(v, (2, 1, 0))[::-1])]:
    for i, c in enumerate(CH):
        t, s = raw[:, i][mask].astype(float), f(a[c])[mask].astype(float)
        print(name, c, 'equal %.3f' % np.mean(t == s), 'corr %.3f' % np.corrcoef(t, s)[0, 1], 'mean tif %.0f czi %.0f' % (t.mean(), s.mean()))
# channel permutation check under zyx
for i in range(4):
    print('tif channel', i, 'best czi channel by corr:', max(CH, key=lambda c: np.corrcoef(raw[:, i][mask].astype(float), np.transpose(a[c], (2, 1, 0))[mask].astype(float))[0, 1]))
