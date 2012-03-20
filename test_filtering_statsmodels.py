# test_filtering_statsmodels.py --- 
# 
# Filename: test_filtering_statsmodels.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Sun Oct 30 14:17:15 2011 (+0530)
# Version: 
# Last-Updated: Sun Oct 30 14:21:50 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 2
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# 
# 
# 

# Change log:
# 
# 
# 

# Code:

import numpy
import pylab
import h5py

import scikits.statsmodel.api as sm


filename = '/media/sda6/cortical_data/2011_10_21/data_20111021_143831_21310.h5'
fhandle = h5py.File(filename, 'r')
datanode = fhandle['/lfp/electrode_1000um']
data = numpy.zeros(3999)
data[:] = datanode[1:4000] # first entry is 0.0 causing errors in analysis
sampling_interval = fhandle.attrs['plotdt']



# 
# test_filtering_statsmodels.py ends here
