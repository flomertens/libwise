'''
Created on Jun 11, 2012

@author: fmertens
'''

import libwise
import glob
from setuptools import setup, find_packages


setup(
    name = 'libwise',
    version = '%s' % libwise.get_version(),
    description = 'Various utilities for the WISE package',
    url = 'https://github.com/flomertens/libwise',
    author = 'Florent Mertens',
    author_email = 'flomertens@gmail.com',
    license='GPL2',

    include_package_data=True,
    packages=find_packages(),
    scripts=glob.glob('scripts/*')
)

