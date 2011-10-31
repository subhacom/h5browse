# analyzer.py --- 
# 
# Filename: analyzer.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sat Oct 29 16:03:56 2011 (+0530)
# Version: 
# Last-Updated: Sat Oct 29 21:06:09 2011 (+0530)
#           By: subha
#     Update #: 31
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
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.
# 
# 

# Code:

import h5py
import numpy
import scipy.signal as signal
# import nitime


# This is mostly taken from SciPy cookbook FIR filter example.
# See: http://www.scipy.org/Cookbook/FIRFilter
def filter_lfp(datalist, sampling_interval, cutoff):
    """Filters hdf5 array data through a bandpass filter with upper
    cut off frequency of cutoff"""
    nyquist_rate = 0.5/sampling_interval
    width = 10/nyquist_rate
    ripple_db = 60.0
    N, beta = signal.kaiserord(ripple_db, width)
    taps = signal.firwin(N, cutoff/nyquist_rate, window=('kaiser', beta))
    filtered_data_list = []
    for data in datalist:
        if not isinstance(data, numpy.ndarray):
            tmp = numpy.zeros(len(data))
            tmp[:] = data[:]
            data = tmp
        filtered_data_list.append(signal.lfilter(taps, 1.0, data))
    return filtered_data_list


                             


# 
# analyzer.py ends here
