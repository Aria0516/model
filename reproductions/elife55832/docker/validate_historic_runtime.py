"""Fail-fast validation for the reconstructed 2020 sam_spaghetti runtime."""

from __future__ import print_function

import importlib
import json
import platform

import pkg_resources


PACKAGES = [
    "python",
    "numpy",
    "scipy",
    "pandas",
    "scikit-image",
    "scikit-learn",
    "matplotlib",
    "vtk",
    "timagetk",
    "cellcomplex",
    "tissue-analysis",
    "tissue-nukem-3d",
    "tissue-paredes",
    "sam-spaghetti",
]

MODULES = [
    "numpy",
    "scipy",
    "pandas",
    "skimage",
    "sklearn",
    "matplotlib",
    "vtk",
    "timagetk",
    "timagetk.components",
    "timagetk.io",
    "timagetk.algorithms.reconstruction",
    "cellcomplex",
    "tissue_analysis",
    "tissue_nukem_3d",
    "tissue_paredes",
    "sam_spaghetti",
    "sam_spaghetti.detection_quantification",
    "sam_spaghetti.sam_microscopy_loading",
    "sam_spaghetti.sequence_image_registration",
    "sam_spaghetti.sam_sequence_primordia_alignment",
]


def installed_version(distribution_name):
    if distribution_name == "python":
        return platform.python_version()
    try:
        return pkg_resources.get_distribution(distribution_name).version
    except pkg_resources.DistributionNotFound:
        return None


for module_name in MODULES:
    importlib.import_module(module_name)

print(json.dumps({name: installed_version(name) for name in PACKAGES},
                 sort_keys=True, indent=2))
print("HISTORIC_RUNTIME_IMPORTS=PASS")
