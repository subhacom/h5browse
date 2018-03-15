from setuptools import setup, find_packages
import sys, os

try:
    version = open('VERSION').read().strip()
except IOError:
    version = '0.2'

setup(name='h5browse',
      version=version,
      description="h5browse is a utility for browsing HDF5 files.",
      long_description="""\ 
h5browse (formerly dataviz) is a utility for browsing HDF5 files.

It was developed for analyzing neuronal simulation data saved in a
custom format. But the interface is generic enough to display simple
HDF5 files. The tools are totally for neuronal data analysis. But the
plan is to make it a more general tool.

As of 2015-12-21, it supports displaying the tree structure of an HDF5
file, node attributes and dataset contents. You can select arbitrary
fields in a dataset for displaying X-Y plots.

Implementation of editing HDF5 is incomplete.

Note that being based on h5py library it inherits the limitations of
the same.

This is a rewrite of the old code. Replaced PyQwt with
PyQtGraph. Written from scratch in Python 3. Compatible with
Python2.7.

""",
      # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=['Development Status :: 3 - Alpha',
                   'Environment :: X11 Applications :: Qt',
                   'Programming Language :: Python',
                   'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
                   'Intended Audience :: Science/Research',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Topic :: Scientific/Engineering :: Visualization',
               ],
      keywords='hdf5 data plotting analysis',
      author='Subhasis Ray',
      author_email='lastname dot firstname at gmail dot com',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
          'numpy',
          'h5py',
          'pyqtgraph',
      ],
      entry_points={
          'gui_scripts': [
              'h5browse=h5browse.h5browse:main',
          ]
      },
      )
