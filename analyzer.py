# analyzer.py --- 
# 
# Filename: analyzer.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sat Oct 29 16:03:56 2011 (+0530)
# Version: 
# Last-Updated: Tue Dec  6 14:04:21 2011 (+0530)
#           By: subha
#     Update #: 245
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

import os
import h5py
import numpy
import scipy.signal as signal
from datetime import datetime
from collections import defaultdict
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

##############################
# Here I am putting in some scratchpad code to do various infrequent
# things.
##############################
def celltype_synstat(cell_synstat):
    start = datetime.now()
    celltype_syn_map = defaultdict(list)
    ret = {}
    for cell, gbar in cell_synstat.items():
        celltype_syn_map[cell.partition('_')[0]].append(gbar)
    for celltype, gbar_list in celltype_syn_map.items():
        ret[celltype] = (numpy.mean(gbar_list), numpy.std(gbar_list))
    end = datetime.now()
    delta = end - start
    print 'celltype_synstat: %g s' % (delta.days * 86400 + delta.seconds + delta.microseconds * 1e-6)
    return ret
        
def get_synstat(netfile):
    """Get some statistics of the synapses on various cell types."""
    start = datetime.now()
    syn_node = netfile['/network/synapse']
    ampa_list = []
    gaba_list = []
    nmda_list = []
    cell_ampa_map = defaultdict(float)
    cell_nmda_map = defaultdict(float)
    cell_gaba_map = defaultdict(float)    
    # 1. First, we separate out the different kinds of synapses into lists
    # In the new format network file, we have /network/synapse node, which contains rows of:
    # (source_compartment, dest_compartment, type, Gbar, tau1, tau2, Ek)
    for syn_row in syn_node:
        cell_syn_map = None
        if 'ampa' == syn_row[2]:
            cell_syn_map = cell_ampa_map
        elif 'nmda' == syn_row[2]:
            cell_syn_map = cell_nmda_map
        elif 'gaba' == syn_row[2]:
            cell_syn_map = cell_gaba_map
        else:
            print 'Unknown synapse type in row:', syn_row
            continue
        dest_cell = syn_row[1].partition('/')[0]
        cell_syn_map[dest_cell] += syn_row[3]
    end = datetime.now()
    delta = end - start
    print 'get_synstat: %g s' % (delta.days * 86400 + delta.seconds + delta.microseconds * 1e-6)
    return {'ampa': cell_ampa_map, 'nmda': cell_nmda_map, 'gaba': cell_gaba_map}

def dump_synstat(netfile):
    cellmaps = get_synstat(netfile)
    for key, cell_syn_map in cellmaps.items():
        filename = os.path.basename(netfilename)
        filename.replace('.h5.new', '_%s.csv' % (key))
        data = sorted(cell_syn_map.items(), cmp=lambda x, y: cmp(int(x[0].rpartition('_')[-1]), int(y[0].rpartition('_')[-1])))
        numpy.savetxt(filename, numpy.array(data, dtype='a32, f4'), fmt='%s, %g')        
    celltype_ampa_map = celltype_synstat(cellmaps['ampa'])
    celltype_nmda_map = celltype_synstat(cellmaps['nmda'])
    celltype_gaba_map = celltype_synstat(cellmaps['gaba'])
    celltype_syn_map = defaultdict(dict)
    for celltype, value in celltype_ampa_map.items():
        celltype_syn_map[celltype]['ampa'] = value
    for celltype, value in celltype_gaba_map.items():
        celltype_syn_map[celltype]['gaba'] = value
    for celltype, value in celltype_nmda_map.items():
        celltype_syn_map[celltype]['nmda'] = value
    return celltype_syn_map


import sys

if __name__ == '__main__':
    netfilename = sys.argv[1]
    print 'Opening:', netfilename
    netfile = h5py.File(netfilename, 'r')
    stat = dump_synstat(netfile)
    netfile.close()
    for key, value in stat.items():
        print key
        print '--------------'
        for kk, vv in value.items():
            print kk, vv

# 
# analyzer.py ends here
