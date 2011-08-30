# trb_correlate.py --- 
#
# Filename: trb_correlate.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sun Aug 28 14:12:44 2011 (+0530)
# Version: 
# Last-Updated: Tue Aug 30 15:23:38 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 80
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
#  Find cross correlation bewteen cells' Vm series/ spike trains.
# 
# 

# Change log:
# 
# 
# 
# 

# Code:

import h5py
import numpy
from scipy.signal import correlate
from datetime import datetime

def find_xcorr(inputfilename, outputfilename):
    datafile = h5py.File(inputfilename, 'r')
    vmnode = datafile['/Vm']
    vmdata = []
    cellname = []
    start = datetime.now()
    for cell in vmnode:
        cellname.append(cell)
        npdata = numpy.zeros(shape=vmnode[cell].shape, dtype=vmnode[cell].dtype)
        npdata[:] = vmnode[cell][:]
        vmdata.append(npdata)
        # print 'Added Vm of %s' % (cell)
    end = datetime.now()    
    dt = end - start
    print 'Fnished reading Vm data in :', (dt.days*86400 + dt.seconds + 1e-6 * dt.microseconds), 'seconds'
    datafile.close()
    datafile = h5py.File(outputfilename, 'w-')
    corrnode = datafile.create_group('correlations')
    start = datetime.now()
    for ii in range(len(cellname)):
        _start = datetime.now()
        # First subtract mean and divide by standard deviation to
        # regularize the data:
        # http://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves
        first = vmdata[ii] - vmdata[ii].mean()
        first /= first.std()
        for jj in range(ii+1):
            second = vmdata[jj] - vmdata[jj].mean()
            second /= second.std()
            corr = correlate(first, second)
            corrdset = corrnode.create_dataset('%s-%s' % (cellname[ii], cellname[jj]), data=corr, compression='gzip')
            # print 'Saved correlation of Vm [%s -> %s]' % (cellname[ii], cellname[jj])
        _end = datetime.now()
        dt = _end - _start
        print 'Finished saving correlations for:', cellname[ii], 'in', dt.days * 86400 + dt.seconds + 1e-6 * dt.microseconds, 'seconds'
    end = datetime.now()
    dt = end - start
    print 'Finished correlation computation and saving in :', dt.days * 86400 + dt.seconds + dt.microseconds, 'seconds'
    datafile.close()
    

import sys
if __name__ == '__main__':
    datasource = '../py/data/2010_12_01/data_20101201_102647_8854.h5'
    output = 'correlation.h5'
    if len(sys.argv) > 1:
        datasource = sys.argv[1]
    if len(sys.argv) > 2:
        output = sys.argv[2]
    find_xcorr(datasource, output)


# 
# trb_correlate.py ends here
