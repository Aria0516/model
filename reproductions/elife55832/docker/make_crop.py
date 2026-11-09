"""Run inside the historic container. Writes an automatic stand-in for the authors' hand-drawn '-No-organs.tif'
crop: every z slice and channel is kept inside a disc of radius R (um) around the CLV3 centre and set to 0 outside
(the authors' crops are also a single 2D region applied to all slices). The file layout is learnt from the
authors' SAM7 crop so that the unmodified loader reads it back exactly.

python make_crop.py learn <czi> <authors_tif>                 # check the axis mapping and the authors' mask
python make_crop.py crop <czi> <out_tif> [R_um] [channels]     # write a crop and verify it reads back identically
                                                               # channels: comma-separated, default DIIV,DR5,TagBFP,CLV3
"""
import sys

import numpy as np
from scipy import ndimage as nd
from tissue_nukem_3d.microscopy_images import tifffile
from tissue_nukem_3d.microscopy_images.read_microscopy_image import read_czi_image, read_tiff_image

CHANNELS = ['DIIV', 'DR5', 'TagBFP', 'CLV3']


def as_np(img):
    return np.asarray(img.get_array() if hasattr(img, 'get_array') else img)


def to_tif_layout(arrays, channels=CHANNELS):
    """czi-loader arrays (x, y, z) per channel -> ImageJ hyperstack (z, c, y, x)."""
    return np.stack([np.transpose(arrays[c], (2, 1, 0)) for c in channels], axis=1)


def clv3_centre(arrays, vs):
    proj = arrays['CLV3'].max(axis=2).astype(float)                    # (x, y)
    sm = nd.gaussian_filter(proj, sigma=5.0 / vs[0])
    w = np.maximum(sm - 0.5 * sm.max(), 0.0)
    X, Y = np.mgrid[0:proj.shape[0], 0:proj.shape[1]]
    return (w * X).sum() / w.sum(), (w * Y).sum() / w.sum()


if __name__ == '__main__':
    mode, czi = sys.argv[1], sys.argv[2]
    if mode == 'crop' and len(sys.argv) > 5:
        CHANNELS = sys.argv[5].split(',')
    img = read_czi_image(czi, channel_names=CHANNELS)
    vs = tuple(img['TagBFP'].voxelsize)
    arrays = {c: as_np(img[c]) for c in CHANNELS}
    print('czi', czi, 'shape', arrays['TagBFP'].shape, 'voxelsize', vs)
    if mode == 'learn':
        raw = tifffile.imread(sys.argv[3])
        print('authors tif raw shape', raw.shape)
        laid = to_tif_layout(arrays)
        mask = (raw > 0).any(axis=1)                                   # z, y, x
        ok = all(np.array_equal(raw[:, i][mask], laid[:, i][mask]) for i in range(len(CHANNELS)))
        print('authors crop equals czi inside its mask under (x,y,z)->(z,c,y,x):', ok)
        back = read_tiff_image(sys.argv[3], channel_names=CHANNELS)
        b = {c: as_np(back[c]) for c in CHANNELS}
        m3 = np.transpose(mask, (2, 1, 0))
        print('loader view of authors crop equals czi*mask:', all(np.array_equal(b[c], arrays[c] * m3) for c in CHANNELS))
        cx, cy = clv3_centre(arrays, vs)
        yy, xx = np.nonzero(mask.any(axis=0))
        print('CLV3 centre (um) %.1f %.1f; authors mask centroid (um) %.1f %.1f' % (cx * vs[0], cy * vs[1], xx.mean() * vs[0], yy.mean() * vs[1]))
    else:
        out, R = sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 60.0
        cx, cy = clv3_centre(arrays, vs)
        X, Y = np.mgrid[0:arrays['TagBFP'].shape[0], 0:arrays['TagBFP'].shape[1]]
        disc = np.hypot((X - cx) * vs[0], (Y - cy) * vs[1]) <= R          # (x, y)
        cropped = {c: arrays[c] * disc[:, :, None].astype(arrays[c].dtype) for c in CHANNELS}
        tifffile.imsave(out, to_tif_layout(cropped, CHANNELS), imagej=True, resolution=(1.0 / vs[0], 1.0 / vs[1]),
                        metadata={'spacing': vs[2], 'unit': 'micron', 'axes': 'ZCYX'})
        back = read_tiff_image(out, channel_names=CHANNELS)
        same = all(np.array_equal(as_np(back[c]), cropped[c]) for c in CHANNELS)
        print('centre (um) %.1f %.1f, radius %.0f um, kept xy fraction %.3f, reads back identically: %s' % (cx * vs[0], cy * vs[1], R, disc.mean(), same))
        if not same:
            sys.exit(2)
