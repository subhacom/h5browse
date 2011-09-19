# trbutil.py --- 
# 
# Filename: trbutil.py
# Description: 
# Author: subhasis ray
# Maintainer: 
# Created: Fri Jun  5 13:59:40 2009 (+0530)
# Version: 
# Last-Updated: Fri Sep  2 15:08:22 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 34
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
from subprocess import call
import pylab
import gzip
import numpy
from scipy import signal

def almost_equal(left, right, epsilon=1e-6):
    """check if two floats are almost equal"""
    if left == right:
        return True
    if abs(left) > abs(right):
        return (1 - right / left) < epsilon
    else:
        return ( 1 - left / right) < epsilon
#!almost_equal

def nxcorr(a, b, mode='full'):
    """Cross correlation function with normalization: based on the
    patch for correlate in numpy:
    http://projects.scipy.org/numpy/attachment/ticket/1714/correlate.parch"""
    a = (a - numpy.mean(a)) / (numpy.std(a)*len(a))
    b = (b - numpy.mean(b))/numpy.std(b)
    return numpy.correlate(a, b, mode=mode)

def ncc(a, b):
    """Cross correlation using fft. Always does a full xcorr."""
    a = (a - numpy.mean(a))/numpy.std(a)
    b = (b - numpy.mean(b))/numpy.std(b)
    ffta = numpy.fft.fft(a, 2*len(a)-1)
    fftb = numpy.fft.fft(b, 2*len(b)-1)
    res = numpy.fft.ifft(ffta * numpy.conj(fftb)).real
    res = numpy.fft.fftshift(res)/(len(a) - 1)
    return res


# 
# trbutil.py ends here
