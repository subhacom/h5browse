from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='h5browse',
      version=version,
      description="h5browse is a utility for viewing HDF5 datasets.",
      long_description="""\ 
h5browse is a utility for viewing HDF5 datasets.

It was developed for analyzing neuronal simulation data saved in a
custom format. But the interface is generic enough to display simple
HDF5 files. The tools are totally for neuronal data analysis. But the
plan is to make it a more general tool.

This is a rewrite of the old code of dataviz. Replaced PyQwt with PyQtGraph.

It uses  Python 3.x, numpy, PyQt5, h5py, PyQtGraph.

Written from scratch in Python 3. Compatible with Python2.7.

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
