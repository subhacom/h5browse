# trb_correlate.py --- 
#
# Filename: trb_correlate.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sun Aug 28 14:12:44 2011 (+0530)
# Version: 
# Last-Updated: Mon Aug 29 11:37:12 2011 (+0530)
#           By: subha
#     Update #: 70
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
        for jj in range(ii):
            corr = numpy.correlate(vmdata[ii], vmdata[jj])
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
