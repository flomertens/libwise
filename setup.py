'''
Created on Jun 11, 2012

@author: fmertens
'''

from setuptools import setup, find_packages, Extension
from Cython.Distutils import build_ext
import numpy as np


ext_nputils_c = Extension(
    "libwise.nputils_c",
    sources = ["libwise/nputils_c.pyx", "libwise/nputils.c"],
    include_dirs = ["libwise", np.get_include()]
    )

setup(
    name = 'libwise',
    version = '0.1',
    description = 'Various utilities for the WISE package',
    url = 'https://github.com/flomertens/libwise',
    author = 'Florent Mertens',
    author_email = 'flomertens@gmail.com',
    license='GPL2',

    include_package_data=True,
    packages=find_packages(),
    # package_data = {'libcorot': ['presets/*.preset', 'ressource/*.png', 
    #                              'ressource/*.svg', 'ressource/*.gif']},

    cmdclass = {'build_ext': build_ext},
    ext_modules = [ext_nputils_c]
)

