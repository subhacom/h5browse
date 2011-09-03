# trb_correlate.py --- 
#
# Filename: trb_correlate.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sun Aug 28 14:12:44 2011 (+0530)
# Version: 
# Last-Updated: Sat Sep  3 12:23:58 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 286
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

import random
import h5py
import numpy
from scipy.signal import correlate
from datetime import datetime
import tables
from util import ncc

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
    print 'Finished reading Vm data in :', (dt.days*86400 + dt.seconds + 1e-6 * dt.microseconds), 'seconds'
    datafile.close()
    start = datetime.now()
    for ii in range(len(cellname)):
        _start = datetime.now()
        filename = '%s_%s.h5' % (outputfilename, cellname[ii])
        print 'Creating:', filename
        outfile = h5py.File(filename, 'w-')
        corrnode = outfile.create_group('correlations_%s' % cellname[ii])
        # First subtract mean and divide by standard deviation to
        # regularize the data:
        # http://stackoverflow.com/questions/6157791/find-phase-difference-between-two-inharmonic-waves
        first = vmdata[ii] - vmdata[ii].mean()
        first /= first.std()
        for jj in range(ii, len(cellname)):
            second = vmdata[jj] - vmdata[jj].mean()
            second /= second.std()
            corr = correlate(first, second, 'same')
            corrdset = corrnode.create_dataset('%s' % (cellname[jj]), data=corr)
            # print 'Saved correlation of Vm [%s -> %s]' % (cellname[ii], cellname[jj])
        _end = datetime.now()
        dt = _end - _start
        outfile.close()
        print 'Finished saving correlations for:', cellname[ii], 'in', dt.days * 86400 + dt.seconds + 1e-6 * dt.microseconds, 'seconds'
    end = datetime.now()
    dt = end - start
    print 'Finished correlation computation and saving in :', dt.days * 86400 + dt.seconds + dt.microseconds, 'seconds'
    outfile.close()

def save_xcorr_h5py(datafilename, netfilename, outfilename, node='Vm', numcells=-1):
    """Same as save_xcorr_pytables using h5py. For comparing h5py with
    pytables."""
    print 'save_xcorr_h5py'
    t_start = datetime.now()
    datafile = h5py.File(datafilename, 'r')
    netfile = h5py.File(netfilename, 'r')
    outfile = h5py.File(outfilename, 'w')
    simtime = None
    plotdt = None
    timestamp = None
    try:
        simtime = datafile.attrs['simtime']
    except KeyError:
        pass
    try:        
        plotdt = datafile.attrs['plotdt']
    except KeyError:
        pass
    try:
        timestamp = datafile.attrs['timestamp']
    except KeyError:
        pass
    outfile.attrs['TITLE'] = 'Correlation of data with time stamp: %s' % (timestamp)
    datanode = datafile['/%s' % (node)]
    cell = []
    vmdata = []
    for data in datanode:
        if node == 'Vm':
            cellname = data[:len(data) - 3] # remove trailing '_Vm'
            cell.append(cellname)
            nparray = numpy.zeros(shape=datanode[data].shape, dtype=datanode[data].dtype)
            nparray[:] = datanode[data][:]
            vmdata.append(nparray)
    t_end = datetime.now()
    t_delta = t_end - t_start
    print 'Finished reading data in %g s' % (t_delta.days * 86400 + t_delta.seconds + t_delta.microseconds * 1e-6)
    if simtime is None:
        simtime = 1.0 * len(vmdata[0])
    if plotdt is None:
        plotdt = 1.0
    if numcells > 0:
        indices = random.sample(range(len(cell)), numcells)
        cell = [cell[index] for index in indices]
        vmdata = [vmdata[index] for index in indices]
    t_start = datetime.now()
    lags = 2 * int(simtime/plotdt) - 1
    time = numpy.fft.fftshift(numpy.fft.fftfreq(lags, 1/(plotdt*lags)))
    corrgroup = outfile.create_group('/%s' % (node))
    timearray = corrgroup.create_dataset('t', data=time, compression='gzip', compression_opts=9)
    for ii in range(len(cell)):
        left = vmdata[ii]
        for jj in range(len(cell)):
            right = vmdata[jj]
            corr = ncc(left, right)
            corrarray = corrgroup.create_dataset('%s-%s' % (cell[ii], cell[jj]), data=corr)
    outfile.close()
    datafile.close()
    netfile.close()
    t_end = datetime.now()
    t_delta = t_end - t_start
    print 'Computed and saved correlatioons in %g seconds' % (t_delta.days * 86400 + t_delta.seconds + t_delta.microseconds * 1e-6)
    

def save_xcorr_pytables(datafilename, netfilename, outfilename, node='Vm', numcells=-1):
    """Save the cross correlation. I am hoping that pytables will give
    better performance in disk space.

    datafilename -- path of file containing data.

    netfilename -- path of file containing network structure.

    outfilename -- path of output file.

    node -- what node to look into for datasets. Default is /Vm

    numcells -- number of cells among which cross correlation is to be
    computed. if -1, all cells in datafile are used.

    """
    print 'save_xcorr_pytables'
    t_start = datetime.now()
    datafile = tables.openFile(datafilename, mode='r')
    netfile = tables.openFile(netfilename, mode='r')
    outfilter = tables.Filters(complevel=9, complib='bzip2', fletcher32=True)
    outfile = tables.openFile(outfilename, mode='w', filters=outfilter)
    simtime = None
    plotdt = None
    timestamp = None
    if hasattr(datafile.root._v_attrs, 'simtime'):
        simtime = datafile.root._v_attrs.simtime
    if hasattr(datafile.root._v_attrs, 'plotdt'):
        plotdt = datafile.root._v_attrs.plotdt
    if hasattr(datafile.root._v_attrs, 'timestamp'):
        timestamp = datafile.root._v_attrs.timestamp
        outfile.title = 'Correlation of data with time stamp: %s' % (timestamp)
    datanode = datafile.getNode('/', node)
    cell = []
    vmdata = []
    for data in datanode:
        if node == 'Vm':
            cellname = data.name[:len(data.name) - 3] # remove trailing '_Vm'
            cell.append(cellname)
            vmdata.append(data.read())
    t_end = datetime.now()
    t_delta = t_end - t_start
    print 'Finished reading data in %g s' % (t_delta.days * 86400 + t_delta.seconds + t_delta.microseconds * 1e-6)
    if simtime is None:
        simtime = 1.0 * len(vmdata[0])
    if plotdt is None:
        plotdt = 1.0
    if numcells > 0:
        indices = random.sample(range(len(cell)), numcells)
        cell = [cell[index] for index in indices]
        vmdata = [vmdata[index] for index in indices]
    t_start = datetime.now()
    lags = 2*int(simtime/plotdt)-1
    time = numpy.fft.fftshift(numpy.fft.fftfreq(lags, 1/(plotdt*lags)))
    corrgroup = outfile.createGroup(outfile.root, node, 'Correlation between %s series' % (node))
    timearray = outfile.createCArray(corrgroup, 't', tables.FloatAtom(), time.shape)
    timearray[:] = time[:]
    for ii in range(len(cell)):
        left = vmdata[ii]
        for jj in range(len(cell)):
            right = vmdata[jj]
            corr = ncc(left, right)
            corrarray = outfile.createCArray(corrgroup, '%s__%s' % (cell[ii], cell[jj]), tables.FloatAtom(), corr.shape)
            corrarray[:] = corr[:]
    outfile.close()
    datafile.close()
    netfile.close()
    t_end = datetime.now()
    t_delta = t_end - t_start
    print 'Computed and saved correlatioons in %g seconds' % (t_delta.days * 86400 + t_delta.seconds + t_delta.microseconds * 1e-6)

import sys
if __name__ == '__main__':
    datafilename = '../py/data/2010_12_01/data_20101201_102647_8854.h5'
    netfilename = '../py/data/2010_12_01/network_20101201_102647_8854.h5'
    outfilename = 'correlation.h5'
    numcells = 5
    if len(sys.argv) > 1:
        datafilename = sys.argv[1]
    if len(sys.argv) > 2:
        netfilename = sys.argv[2]
    if len(sys.argv) > 3:
        outfilename = sys.argv[3]
    if len(sys.argv) > 4:
        numcells = int(sys.argv[4])
    # find_xcorr(datafilename, outfilename)
    save_xcorr_pytables(datafilename, netfilename, 'pytables_%s' % (outfilename), numcells=numcells)
    save_xcorr_h5py(datafilename, netfilename, 'h5py_%s' % (outfilename), numcells=numcells)


# 
# trb_correlate.py ends here
