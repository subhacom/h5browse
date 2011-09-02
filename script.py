# script.py --- 
# 
# Filename: script.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Thu Sep  1 11:59:36 2011 (+0530)
# Version: 
# Last-Updated: Fri Sep  2 18:15:26 2011 (+0530)
#           By: Subhasis Ray
#     Update #: 161
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

from datetime import datetime
from util import *

import random
import numpy
import h5py
import pylab
from numpy import fft
import igraph as ig

class XcorrPlotter:
    def __init__(self, filename='../py/data/data_20101201_102647_8854.h5'):
        self.fd = h5py.File(filename, 'r')
        self.vmnode = self.fd['/Vm']
        self.suppyrRS = [name for name in self.vmnode.keys() if name.startswith('SupPyrRS')]
        self.left = random.sample(self.suppyrRS, 10)
        self.right = random.sample(self.suppyrRS, 10)


    def plotxcorr(self, i, j, offset=1000):
        self.ldata = self.vmnode[self.left[i]]
        self.rdata = self.vmnode[self.right[j]]
        self.lseries = numpy.zeros(len(self.ldata) - offset, dtype=self.ldata.dtype)
        self.rseries = numpy.zeros(len(self.rdata) - offset, dtype=self.rdata.dtype)
        self.lseries[:] = self.ldata[offset:]
        self.rseries[:] = self.rdata[offset:]
        self.value = ncc(self.lseries, self.rseries)
        self.t = fft.fftshift(fft.fftfreq(len(self.value), 1.0/len(self.value)))
        pylab.plot(self.t, self.value, label='%s->%s' % (self.left[i], self.right[j]))

    def get_left_cellname(self, index):
        return self.left[index][:len(self.left[index])-3]
    
    def get_right_cellname(self, index):
        return self.right[index][:len(self.right[index])-3]

    def __del__(self):
        self.fd.close()

class NetAnalyzer:
    def __init__(self, filename='../py/data/network_20101201_102647_8854.h5'):
        """Find the connectivity between pairs of cells."""
        self.fd = h5py.File(filename, 'r')
        celltype = sorted(self.fd['/network/celltype'], key=lambda x: x[1])
        self.cellindex = {}
        self.celllist = []
        start = 0
        for cell in celltype:
            for ii in range(cell[0]):
                cellname = '%s_%d' % (cell[2], ii)
                self.celllist.append(cellname)
                self.cellindex[cellname] = start + ii
            start += cell[0] # 0-th column is count for the celltype
        print 'Finished reading cell list'
        cellnet = self.fd['/network/cellnetwork']
        t_start = datetime.now()
        ampa = cellnet['gampa']
        self.ampanet = ig.Graph(0, directed=True)
        self.ampanet.add_vertices(len(self.celllist))
        self.ampanet.vs['name'] = self.celllist
        ampa_edges = [(int(entry[0]), int(entry[1])) for entry in ampa]
        self.ampanet.add_edges(ampa_edges)
        self.ampanet.es['weight'] = [entry[2] for entry in ampa]
        t_end = datetime.now()
        t_delta = t_end - t_start
        print 'Finished creating AMPA net in %g s' % (t_delta.days * 86400.0 + t_delta.seconds + 1e-6 * t_delta.microseconds)
        t_start = datetime.now()
        nmda = cellnet['gnmda']
        self.nmdanet = ig.Graph(0, directed=True)
        self.nmdanet.add_vertices(len(self.celllist))
        nmda_edges = [(int(entry[0]), int(entry[1])) for entry in nmda]
        self.nmdanet.add_edges(nmda_edges)
        self.nmdanet.es['weight'] = [entry[2] for entry in nmda]
        t_end = datetime.now()
        t_delta = t_end - t_start
        print 'Finished creating GABA net in %g s' % (t_delta.days * 86400.0 + t_delta.seconds + 1e-6 * t_delta.microseconds)
        t_start = datetime.now()
        gaba = cellnet['ggaba']
        self.gabanet = ig.Graph(0, directed=True)
        self.gabanet.add_vertices(len(self.celllist))
        gaba_edges = [(int(entry[0]), int(entry[1])) for entry in gaba]
        self.gabanet.add_edges(gaba_edges)
        self.gabanet.es['weight'] = [entry[2] for entry in gaba]
        t_end = datetime.now()
        t_delta = t_end - t_start
        print 'Finished creating GABA net in %g s' % (t_delta.days * 86400.0 + t_delta.seconds + 1e-6 * t_delta.microseconds)


    def connected(self, cell1, cell2, mode=ig.ALL):
        if ig.__version__ < '0.6':
            print 'igraph version:', ig.__version__
            print 'returning edge disjoint paths'
        v1 = self.cellindex[cell1]
        v2 = self.cellindex[cell2]
        return (self.ampanet.shortest_paths(source=[v1], target=[v2], weights=None, mode=mode,
                self.nmdanet.shortest_paths(source=[v1], target=[v2], weights=None, mode=mode),
                self.gabanet.shortest_paths(source=[v1], target=[v2], weights=None, mode=mode))

# 
# script.py ends here
