'''
Created on Jun 11, 2012

@author: fmertens
'''

from setuptools import setup, find_packages, Extension


setup(
    name = 'libwise',
    version = '0.2',
    description = 'Various utilities for the WISE package',
    url = 'https://github.com/flomertens/libwise',
    author = 'Florent Mertens',
    author_email = 'flomertens@gmail.com',
    license='GPL2',

    include_package_data=True,
    packages=find_packages(),
    # package_data = {'libcorot': ['presets/*.preset', 'ressource/*.png', 
    #                              'ressource/*.svg', 'ressource/*.gif']},

)

