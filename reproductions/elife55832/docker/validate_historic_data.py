"""Read one official E27/SAM7 CZI with the historical microscopy stack."""

from __future__ import print_function

import json
import sys

from tissue_nukem_3d.microscopy_images.read_microscopy_image import read_czi_image


CHANNELS = ["DIIV", "DR5", "TagBFP", "CLV3"]


images = read_czi_image(sys.argv[1], channel_names=CHANNELS)
summary = {}
for name in CHANNELS:
    image = images[name]
    summary[name] = {
        "dtype": str(image.dtype),
        "shape": list(image.shape),
        "voxelsize": [float(value) for value in image.voxelsize],
    }

print(json.dumps(summary, indent=2, sort_keys=True))
print("HISTORIC_CZI_READ=PASS")
