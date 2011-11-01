# analyzer.py --- 
# 
# Filename: analyzer.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sat Oct 29 16:03:56 2011 (+0530)
# Version: 
# Last-Updated: Tue Nov  1 17:37:24 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 53
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
from datetime import datetime
# import nitime


# This is mostly taken from SciPy cookbook FIR filter example.
# See: http://www.scipy.org/Cookbook/FIRFilter
def fir_filter(datalist, sampling_interval, cutoff=450.0, rolloff=10.0):
    """Filters hdf5 array data through a bandpass filter with upper
    cut off frequency of cutoff"""
    if not datalist:
        print 'Empty data list'
        return []
    nyquist_rate = 0.5/sampling_interval
    width = rolloff/nyquist_rate
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

def blackmann_windowedsinc_filter(datalist, sampling_interval, cutoff=450.0, rolloff=10.0):
    print 'Sampling rate:', 1/sampling_interval
    print 'Cutoff frequency:', cutoff
    print 'Rolloff frequency:', rolloff
    if not datalist:
        print 'Empty data list'
        return []
    start = datetime.now()
    m = int(4.0 / (rolloff * sampling_interval) - 0.5)
    if m%2 == 1:
        m += 1
    cutoff = cutoff * sampling_interval
    indices = numpy.linspace(0.0, m+1, m+1)
    syncwin = 2 * cutoff * numpy.sinc(2*cutoff*(indices-m/2))
    blackmann = 0.42 - 0.5 * numpy.cos(2 * numpy.pi * indices / m) + 0.08 * numpy.cos(4 * numpy.pi * indices / m)
    lowpass = syncwin * blackmann
    lowpass = lowpass/ numpy.sum(lowpass)
    filtered_data_list = []
    for data in datalist:
        filtered_data = numpy.convolve(lowpass, data, mode='same')
        filtered_data_list.append(filtered_data)
    end = datetime.now()
    delta = end - start
    print 'blackmann_windowedsinc_filter:', '%g s for %d arrays of length %d' % (delta.days * 86400 + delta.seconds + delta.microseconds * 1e-6, len(datalist), len(datalist[0]))
    return filtered_data_list


# 
# analyzer.py ends here
