# trbutil.py --- 
# 
# Filename: trbutil.py
# Description: 
# Author: subhasis ray
# Maintainer: 
# Created: Fri Jun  5 13:59:40 2009 (+0530)
# Version: 
# Last-Updated: Tue Apr  3 16:34:43 2012 (+0530)
#           By: subha
#     Update #: 72
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
import h5py as h5
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

def print_diff(message, left, right, ldiff, rdiff):
    print '%s: %s [%s] <-> %s [%s]' % (message, left.name, ldiff, right.name, rdiff)
    
def check_network_identity(left, right):
    """Compare two hdf5 network files for equality."""
    ret = True
    if type(left) != type(right):
        print_diff('Different types:', left, right, left.__class__.__name__, right.__class__.__name__)
        return False
    if isinstance(left, h5.Group):
        lkeys = sorted(left.keys())
        rkeys = sorted(right.keys())
        if len(lkeys) != len(rkeys):
            print_diff('Different childcount:', left, right,  len(lkeys), len(rkeys))
            return False
        for ii in range(len(lkeys)):
            if lkeys[ii] != rkeys[ii]:
                print_diff('Different children:', left, right, lkeys[ii], rkeys[ii])
                ret = False
            next_ret = check_network_identity(left[lkeys[ii]], right[rkeys[ii]])
            if ret:
                ret = next_ret
        return ret
    if isinstance(left, h5.Dataset):
        if left.shape != right.shape:
            print_diff('Datasets of unequal length:', left, right, len(left), len(right))
            return False
        ldata = left[:]
        rdata = right[:]
        if ldata.dtype != rdata.dtype:
            print_diff('Datatypes don\'t match:', left, right, ldata.dtype, rdata.dtype)
            ret = False
        else:
            fnames = ldata.dtype.names
            if fnames is not None:
                for fname in fnames:
                    for ii in range(min(len(ldata), len(rdata))):
                        res = ldata[fname][ii] == rdata[fname][ii]
                        if isinstance(res, numpy.ndarray):
                            res = res.all()
                        if not res:
                            print_diff('Entries do not match (%s[%d])' % (fname, ii), left, right, str(ldata[fname][ii]), str(rdata[fname][ii]))
                            ret = False
            else:
                for ii in range(min(len(ldata), len(rdata))):
                    res = ldata[ii] == rdata[ii]
                    if isinstance(res, numpy.ndarray):
                        res = res.all()
                    if not res:
                        print_diff('Entries do not match [%d])' % (ii), left, right, str(ldata[ii]), str(rdata[ii]))
                        ret = False
    return ret
            



# 
# trbutil.py ends here
