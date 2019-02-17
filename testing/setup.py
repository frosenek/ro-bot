#!/usr/bin/python
# -*- coding: utf-8 -*-

import setuptools

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

import numpy as np

# must use extensions for specifiying include_dirs for whatever reasons
extensions = [
    Extension(
        "world",
        ["world.pyx"],
        include_dirs=[np.get_include()],
        define_macros=[('NPY_NO_DEPRECATED_API', 'NPY_1_7_API_VERSION')],
    )
]

setup(
    ext_modules=cythonize(extensions, language_level=3)
)
