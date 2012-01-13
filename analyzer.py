# analyzer.py --- 
# 
# Filename: analyzer.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sat Oct 29 16:03:56 2011 (+0530)
# Version: 
# Last-Updated: Fri Jan 13 16:55:55 2012 (+0530)
#           By: subha
#     Update #: 315
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


def is_spiking(filehandle, cellname, ignore_time):
    """Check if a cell is spiking.

    filehandle -- data file (h5py.File object opened readonly)
    
    cellname -- cell whose spiking is to be checked

    ignore_time -- any spiking before this time will be ignored. This
    is because often there is a spike at time 0 due to imbalance in
    initial Vm and resting membrane potential.
    """
    spike_times = numpy.array(filehandle['spikes'][cellname])
    for time in spike_times:
        if time > ignore_time:
            return True
    return False

def get_spiking_cellnames(filehandle, celltype, ignoretime):
    ret = []
    for spiking_cell in filehandle['spikes']:
        if spiking_cell.startswith(celltype) and is_spiking(filehandle, spiking_cell, ignoretime):
            ret.append(spiking_cell)
    return ret
    
def find_presynaptic_spike_sources(netfile, datafile, cellname, ignore_time):
    """Return a list of presynaptic cells that fired.

    netfile -- network file [should be in the new format where source compartment and target compartments are listed under /network/synapse

    datafile -- file containing spike data under /spikes

    cellname -- cell whose presynaptic neighbours are to be investigated.

    ignore_time -- ignore spikes before this time    
    
    """
    source_cells = []
    spiking_sources = []
    for item in netfile['/network/synapse']:
        target_cell = item[1].partition('/')[0]        
        if target_cell == cellname:
            source_cells.append(item[0].partition('/')[0])
    for cell in source_cells:
        if is_spiking(datafile, cell, ignore_time):
            spiking_sources.append(cell)
    return spiking_sources

def get_pre_spikes(netfile, datafile, spiking_cells, ignore_time):
    """Get the datasets for all presynaptic entites that spiked for
    the cells in spiking_cells list"""
    src_set = defaultdict(list)
    ret = {}
    for cell in spiking_cells:
        sources = find_presynaptic_spike_sources(netfile, datafile, cell, ignore_time)
        for src in sources:
            if src not in src_set[cell]:
                src_set[cell].append(src)
        ectopic_src = 'ectopic_'+cell
        if is_spiking(datafile, ectopic_src, ignore_time):
            src_set[cell].append(ectopic_src)
    for key, value in src_set.items():
        ret[key] = [datafile['spikes'][v] for v in value]
    return ret
            

def plot_spikes_and_prespikes(netfile, datafile, spiking_cells, ignore_time):
    pre_spikes_map = get_pre_spikes(netfile, datafile, spiking_cells, ignore_time)
    for ii in range(len(spiking_cells)):
         data = datafile['spikes'][spiking_cells[ii]]
         plot(data, ones(len(data)) * (1.0+ii), 'r^-', label=spiking_cells[ii])
         pre_data = []
         try:
             pre_data  = pre_spikes_map[spiking_cells[ii]]
         except KeyError:
             continue
         jj = 1
         for value in pre_data:
             if not value:
                 continue
             symbol = 'go'
             if 'ectopic_' in value.name:
                 symbol = 'bv'
             plot(value, ones(len(value)) * (ii + jj * 1.0 / (1+len(pre_spikes_map[spiking_cells[ii]]))),  symbol, label=value.name)
             jj += 1

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

