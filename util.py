# trbutil.py --- 
# 
# Filename: trbutil.py
# Description: 
# Author: subhasis ray
# Maintainer: 
# Created: Fri Jun  5 13:59:40 2009 (+0530)
# Version: 
# Last-Updated: Thu Mar 21 16:40:13 2013 (+0530)
#           By: subha
#     Update #: 95
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
import numpy as np
import os
import csv
from scipy.signal import gaussian
from scipy.ndimage import filters

datadir = '/data/subha/rsync_ghevar_cortical_data_clone'
from datetime import datetime
def makepath(fname, datadir=datadir):
    """Create the full path from file name and datadir."""
    ts = fname.partition('_')[-1].partition('.')[0].rpartition('_')[0]
    ts = datetime.strptime(ts, '%Y%m%d_%H%M%S')
    dirname = ts.strftime('%Y_%m_%d')
    path = os.path.join(datadir, dirname, fname)
    return path


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

def smooth_gaussian(y, binsize, twindow=100e-3, std=1.0):
    """Do gaussian smoothing with window size `twindow`. Number of points
    is determined using interval between points given by binsize.

    """
    size = int(twindow/binsize)
    b = gaussian(size, std)
    ga = filters.convolve1d(y, b/b.sum())
    # plt.figure()
    # plt.plot(ga)    
    # plt.show()
    return ga
        


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
            
def get_contiguous_regions(indices):
    """Get the starts and ends of contiguous indices.

    indices: array of index values, with possibly some entries
    missing.

    startendarray:

    a 2D array where row[i] = (start[i], end[i]) for the ith
    contiguous series of values.
    Example:

    indices = array([0, 1, 2, 4, 5, 8, 9])
    
    get_contiguous_regions(indices)

    array([[0, 3],
           [4, 6],
           [8, 10]]) 

    """
    brk = np.nonzero(np.diff(indices) > 1)[0]
    return np.c_[np.r_[indices[0], indices[brk+1]], np.r_[indices[brk], indices[-1]]]

def load_celltype_colors(filename='~/Documents/thesis/data/colorscheme.txt'):
    filename = os.path.normpath(os.path.expanduser(os.path.expandvars(filename)))
    colordict = {}
    with open(filename) as fd:
        reader = csv.reader(fd, delimiter=' ', quotechar="'")
        for tokens in reader:
            colordict[tokens[0]] = tokens[1]
    return colordict

# 
# trbutil.py ends here
