'''
Created on Jun 11, 2012

@author: fmertens
'''

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext
import numpy as np


ext_modules = [Extension(
    "utils/nputils_c",
    sources=["utils/nputils_c.pyx", "utils/nputils.c"])]

setup(
    cmdclass={'build_ext': build_ext},
    include_dirs=[np.get_include()],
    ext_modules=ext_modules
)

