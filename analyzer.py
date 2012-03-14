# analyzer.py --- 
# 
# Filename: analyzer.py
# Description: 
# Author: 
# Maintainer: 
# Created: Sat Oct 29 16:03:56 2011 (+0530)
# Version: 
# Last-Updated: Mon Mar 12 16:08:59 2012 (+0530)
#           By: subha
#     Update #: 1305
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
import pylab
import scipy.signal as signal
from datetime import datetime, timedelta
from collections import defaultdict
# import nitime
import scipy.optimize as opt
import igraph as ig

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
    
def get_presynaptic_cells(netfile, cellname):
    """Return a list of all presynaptic cell names"""
    precells = set()
    for item in netfile['/network/synapse']:
        if cellname in item[1]:
            precells.add(item[0].partition('/')[0])
    return precells

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

def get_simtime(filehandle):
    ret = None
    for row in filehandle['runconfig']['scheduling']:
        if row[0] == 'simtime':
            ret = float(row[1])
    return ret

def get_simdt(filehandle):
    ret = None
    for row in filehandle['runconfig']['scheduling']:
        if row[0] == 'simdt':
            ret = float(row[1])
    return ret

def get_plotdt(filehandle):
    ret = None
    for row in filehandle['runconfig']['scheduling']:
        if row[0] == 'plotdt':
            ret = float(row[1])
    return ret

def get_bgtimes(filehandle):
    stim_bg = filehandle['stimulus']['stim_bg'][:]
    simtime = get_simtime(filehandle)
    return numpy.nonzero(numpy.diff(stim_bg) > 0.0)[0] * simtime / len(stim_bg)

def get_probetimes(filehandle):
    stim_probe = filehandle['stimulus']['stim_probe'][:]
    simtime = get_simtime(filehandle)
    indices = numpy.nonzero(numpy.diff(stim_probe) > 0.0)
    return indices[0] * simtime / len(stim_probe)

def get_affected_cells(datafile, netfile, timewin):
    stim_dest = get_stimulated_cells(netfile)
    print 'Stimulus destinations'
    for key, value in stim_dest.items():
        print key, ':',
        for cellname in value:
            print cellname, ',',
        print
    background_times = get_bgtimes(datafile)
    probe_times = get_probetimes(datafile)
    fired_on_bg = set()
    fired_on_probe = set()
    for cellname in datafile['/spikes']:
        spike_times = datafile['/spikes'][cellname][:]
        print cellname, spike_times.shape[0]
        if spike_times[-1] < probe_times[0]:
            continue        
        for ii in range(len(probe_times)/2):
            probe_time = probe_times[2*ii]
            bg_time = background_times[4*ii]
            print bg_time, probe_time
            indices_in_window = numpy.nonzero(numpy.logical_and(spike_times > bg_time, spike_times < bg_time+timewin))[0]
            if len(indices_in_window) > 0:
                fired_on_bg.add(cellname)
                print 'Fired on bg:', cellname
            indices_in_window = numpy.nonzero(numpy.logical_and(spike_times > probe_time, spike_times < probe_time+timewin))[0]
            if len(indices_in_window) > 0:
                fired_on_probe.add(cellname)
                print 'Fired on bg+probe:', cellname
    return (fired_on_bg, fired_on_probe)
            
def is_connected_to_probed_cell(netfile, cellname):
    stim_dests = get_stimulated_cells(netfile)
    precells = get_presynaptic_cells(netfile, cellname)
    return len(stim_dests['/stim/stim_probe'] & precells) > 0

def get_stimulated_cells(netfile):
    stim_dest = defaultdict(set)
    for row in netfile['stimulus']['connection']:
        # The paths are /model/net/{cellname}/{compname}.
        cellname = row[1].rpartition('/')[0].rpartition('/')[-1]
        stim_dest[row[0]].add(cellname)
    return stim_dest

def find_spikes_by_stim(datafile, netfile, timewindow):
    stim_dest = get_stimulated_cells(netfile)
    bg_times = get_bgtimes(datafile)
    probe_times = get_probetimes(datafile)
    fired_on_bg = set()
    fired_on_probe = set()
    for cellname in datafile['/spikes']:
        spike_times = datafile['/spikes'][cellname][:]
        # print spike_times.shape
        # If the cell did not fire any spike after the first probe
        # pulse, skip it: there is unlikely to be a path from probed
        # cell to this.
        if spike_times[-1] < probe_times[0]:
            continue
        for ii in range(len(probe_times)):
            t_bg = bg_times[2*ii]
            t = probe_times[ii]
            probe_indices = numpy.nonzero(spike_times[numpy.nonzero(spike_times > t)[0]] < t+timewindow)
            bg_indices =  numpy.nonzero(spike_times[numpy.nonzero(spike_times > t_bg)[0]] < t_bg+timewindow)
            if len(probe_indices) > 0:
                fired_on_probe.add(cellname)
            if len(bg_indices) > 0:
                fired_on_bg.add(cellname)
    probe_connected = set()
    for cellname in fired_on_probe:
        # exclude cells that are directly stimulated by the probe stimulus
        if cellname not in stim_dest['/stim/stim_probe'] and cellname not in stim_dest['/stim/stim_bg']:
            probe_connected.add(cellname)
            print 'probe/bg -connected:', cellname
    bg_connected = set()
    for cellname in fired_on_bg:
        # exclude cells that are directly stimulated by the stimulus
        if cellname not in stim_dest['/stim/stim_probe'] and cellname not in stim_dest['/stim/stim_bg']:
            bg_connected.add(cellname)    
    return probe_connected - fired_on_bg

def get_bgstim_aligned_chunks(datafile, cellname):
    ret = []
    spikes = datafile['/spikes']
    simtime = get_simtime(datafile)    
    stimulus_node = datafile['/runconfig/stimulus']
    stimulus_info = {}
    for row in stimulus_node:
        try:
            value = int(row[1])
        except ValueError:
            try:
                value = float(row[1])
            except ValueError:
                value = row[1]
        stimulus_info[row[0]] = value
    stim_width = stimulus_info['bg_interval'] + stimulus_info['pulse_width'] + stimulus_info['isi']
    print cellname, stim_width
    for name in spikes:
        if cellname in name and not name.startswith('ectopic'):
            t_stim = stimulus_info['onset'] + stimulus_info['bg_interval']
            spiketrain = spikes[name][:] - t_stim
            indices = numpy.nonzero(spiketrain > 0)[0]
            while len(indices) > 0:
                spiketrain = spiketrain[indices]
                chunk_indices = numpy.nonzero(spiketrain < stim_width)[0]                
                if len(chunk_indices) > 0:
                    chunk = spiketrain[chunk_indices]
                    ret.append(chunk)
                spiketrain = spiketrain - stim_width
                indices = numpy.nonzero(spiketrain > 0)[0]
    return (ret, stim_width)
    
def calculate_psth(datafile, cellname, binsize):
    spikes = datafile['/spikes']
    simtime = get_simtime(datafile)    
    stimulus_node = datafile['/runconfig/stimulus']
    stimulus_info = {}
    for row in stimulus_node:
        try:
            value = int(row[1])
        except ValueError:
            try:
                value = float(row[1])
            except ValueError:
                value = row[1]
        stimulus_info[row[0]] = value
    stim_width = stimulus_info['bg_interval'] + stimulus_info['pulse_width'] + stimulus_info['isi']
    psth = numpy.zeros(int(stim_width/binsize))
    bins = numpy.arange(0, stim_width, binsize)
    for name in spikes:
        if cellname in name and not name.startswith('ectopic'):
            t_stim = stimulus_info['onset'] + stimulus_info['bg_interval']
            spiketrain = spikes[name][:] - t_stim
            indices = numpy.nonzero(spiketrain > 0)[0]
            while len(indices) > 0:
                spiketrain = spiketrain[indices]
                chunk_indices = numpy.nonzero(spiketrain < stim_width)[0]                
                if len(chunk_indices) > 0:
                    chunk = spiketrain[chunk_indices]
                    psth += numpy.histogram(chunk, bins)[0]
                spiketrain = spiketrain - stim_width
                indices = numpy.nonzero(spiketrain > 0)[0]
    return (psth, bins)

def plot_psth(datafile, celltypes, binsize):
    celltype_st_map = {}
    numrows = len(celltypes)
    w = 1    
    ii = 0
    for celltype in celltypes:
        x, w, = get_bgstim_aligned_chunks(datafile, celltype)
        x = numpy.concatenate(x)
        x.sort()
        celltype_st_map[celltype] = x
        ii += 1
        pylab.subplot(numrows, 1, ii)
        # pylab.title(celltype)
        pylab.hist(x, numpy.arange(0, w, binsize), label=celltype)
        pylab.legend()
    pylab.show()
    return celltype_st_map

def get_stiminfo_dict(fhandle):
    stimulus_node = fhandle['/runconfig/stimulus']
    stimulus_info = {}
    for row in stimulus_node:
        try:
            value = int(row[1])
        except ValueError:
            try:
                value = float(row[1])
            except ValueError:
                value = row[1]
        stimulus_info[row[0]] = value
    return stimulus_info

def extract_chunks(spiketrain, stimstart, stimwidth):
    ret = []
    spiketrain = spiketrain - stimstart
    indices = numpy.nonzero(spiketrain > 0)[0]
    while len(indices) > 0:
        spiketrain = spiketrain[indices]
        indices = numpy.nonzero(spiketrain < stimwidth)[0]
        if len(indices) > 0:
            chunk = spiketrain[indices]
            ret.append(chunk)
        spiketrain = spiketrain - stimwidth
        indices = numpy.nonzero(spiketrain > 0)[0]
    return ret

def chunks_from_multiple_datafile(filenames, celltypes, bg_interval=None, isi=None, pulse_width=None):    
    """Collect spiketimes for each entry in celltypes from all files
    in filenames into chunks aligned with first of the background
    pulse pair."""
    ret = {}
    stim_width_map = {}
    cellcount_map = defaultdict(int)
    for celltype in celltypes:
        ret[celltype] = defaultdict(list)
    for filename in filenames:
        fhandle = h5py.File(filename, 'r')
        simtime = get_simtime(fhandle)    
        stimulus_info = get_stiminfo_dict(fhandle)
        if (bg_interval is not None and isi is not None and pulse_width is not None) and (float(stimulus_info['bg_interval']) != bg_interval or float(stimulus_info['isi']) != isi):
            continue
            
        stim_width = stimulus_info['bg_interval'] + stimulus_info['pulse_width'] + stimulus_info['isi']
        stim_width_map[filename] = stim_width
        t_stim = stimulus_info['onset'] + stimulus_info['bg_interval']
        spikes = fhandle['/spikes']
        for name in spikes:
            for celltype in celltypes:
                if not celltype.startswith('ectopic') and celltype in name:
                    chunks = extract_chunks(spikes[name][:], t_stim, stim_width)
                    ret[celltype][filename] += chunks
                    cellcount_map[celltype] += 1
        fhandle.close()
    return (ret, stim_width_map, cellcount_map)

def psth_multifile(filenames, celltypes, binsize, combined=False, bg_interval=None, isi=None, pulse_width=None):
    numrows = len(celltypes)
    chunks, stimwidths, cellcounts = chunks_from_multiple_datafile(filenames, celltypes, bg_interval=bg_interval, isi=isi, pulse_width=pulse_width)
    for ii in range(len(celltypes)):
        print 'Processing', celltypes[ii]
        pylab.subplot(numrows, 1, ii)
        pylab.title(celltypes[ii])
        x = []
        for filename, chunked_data in chunks[celltypes[ii]].items():
            if len(chunked_data) == 0:
                continue
            tmp = numpy.concatenate(chunked_data)
            print celltypes[ii], filename, tmp.shape
            if len(tmp) == 0:
                continue
            if not combined:
                tmp.sort()
                bins = numpy.arange(0, stimwidths[filename], binsize)
                hist, edges = numpy.histogram(tmp, bins)
                hist = hist / (len(chunked_data) * binsize) # normalize by number of stim presentations and binsize
                tmp = numpy.zeros(len(bins)-1)
                tmp[:len(hist)] = hist[:]
                pylab.bar(bins[:-1], tmp, binsize, label=os.path.basename(filename))
                pylab.xlim(0, edges[-1])
                maxy = pylab.ylim()[1]
                pylab.yticks([int(y) for y in numpy.linspace(0, maxy, 5)])

            else:
                x = numpy.concatenate([x, tmp])
            print 'Processed', filename, len(x)
        if combined:
            if bg_interval is None:
                # print stimwidths.values()
                stim_width = max(stimwidths.values())
            else:
                stim_width = bg_interval + isi + pulse_width
            x.sort()            
            print 'Total number of spikes', len(x)
            bins = numpy.arange(0, stimwidths[filename], binsize)
            hist, edges = numpy.histogram(x, bins)
            hist = hist / (len(chunked_data) * binsize) # normalize by number of stim presentations and binsize
            tmp = numpy.zeros(len(bins)-1)
            tmp[:len(hist)] = hist[:]            
            pylab.bar(bins[:-1], tmp, binsize, label=celltypes[ii])
            pylab.xlim(0, edges[-1])
            maxy = pylab.ylim()[1]
            pylab.yticks([int(y) for y in numpy.linspace(0, maxy, 5)])
        else:
            pylab.legend()
    pylab.subplots_adjust(hspace=1)
    pylab.show()

def get_psth(binsize, timewindow, spiketrains):
    combined_spikes = numpy.concatenate(spiketrains)
    combined_spikes.sort()
    return numpy.histogram(combined_spikes, numpy.arange(0, timewindow, binsize))
    
def cost_psth(binsize, timewindow, spiketrains):
    """Take a binsize and a sequence of spike trains and return PSTH
    from that."""
    num_spike_trains = len(spiketrains)
    hist, edges, = get_psth(binsize, timewindow, spiketrains)
    mean_count = numpy.mean(hist)
    variance_count = numpy.var(hist)
    return (2 * mean_count - variance_count)/(num_spike_trains * binsize)**2
    
def get_optimal_psth_binsize(spiketrain, timewindow, min_binsize, max_binsize):
    xopt, fval, ierr, numfunc, = opt.fminbound(cost_psth, min_binsize, max_binsize, args=(timewindow, spiketrain), full_output=True, disp=3)
    print 'optimal binsize:', xopt, 'cost:', fval, 'error code:', ierr, 'no. of evaluations:', numfunc
    return xopt

            
        
def plot_psth_optimal_binsize(filenames, celltypes, min_binsize, max_binsize, bg_interval, isi, pulse_width):
    stimwidth = bg_interval + isi + pulse_width
    spikechunks, stimwidths, cellcounts, = chunks_from_multiple_datafile(filenames, celltypes, bg_interval, isi, pulse_width)
    spiketrains = defaultdict(list)
    numrows = len(celltypes)
    ii = 1
    for cell in celltypes:        
        for chunks in spikechunks[cell].values():
            spiketrains[cell] += chunks
        print cell, 
        binsize = get_optimal_psth_binsize(spiketrains[cell], stimwidth, min_binsize, max_binsize)
        hist, edges, = get_psth(binsize, stimwidth, spiketrains[cell])
        hist /= (len(spiketrains[cell]) * binsize)
        pylab.subplot(numrows, 1, ii)
        pylab.title(cell)
        pylab.bar(edges[:-1], hist, binsize, label=cell)
        pylab.xlim(0, edges[-1])
        maxy = pylab.ylim()[1]
        pylab.yticks([int(y) for y in numpy.linspace(0, maxy, 5)])
        ii += 1
    pylab.subplots_adjust(hspace=1)
    pylab.show()

def plot_conncounts(netfilepath):
    netfile = h5py.File(netfilepath, 'r')
    syn = numpy.asarray(netfile['/network/synapse'])
    netfile.close()
    conndict = defaultdict(int)
    for row in syn:
        conn = row[0] + '-' + row[1]
        conndict[conn] += 1
    pylab.plot(range(len(conndict)), conndict.values(), '.')
    # pylab.xticks(numpy.array(range(len(syn))), conndict.keys())
    pylab.show()

def plot_cellcell_conncounts(netfilepath):
    """Plot number synapses between each connected cell pair"""
    netfile = h5py.File(netfilepath, 'r')
    syn = numpy.asarray(netfile['/network/synapse'])
    netfile.close()
    conndict = defaultdict(int)
    for row in syn:
        conn = row[0].partition('/')[0] + '-' + row[1].partition('/')[0]
        conndict[conn] += 1
    pylab.plot(range(len(conndict)), conndict.values(), '.')
    pylab.xticks(numpy.array(range(len(syn))), conndict.keys())
    pylab.show()

def get_cellcell_conncounts(netfilepath):
    """Return number synapses between each connected cell pair"""
    netfile = h5py.File(netfilepath, 'r')
    syn = numpy.asarray(netfile['/network/synapse'])
    netfile.close()
    conndict = defaultdict(int)
    for row in syn:
        conn = row[0].partition('/')[0] + '-' + row[1].partition('/')[0]
        conndict[conn] += 1
    return conndict

def find_bad_files(netfilelist):
    """A counterpart of plot_conncounts to find out files that have
    compartment-pairs with excess connections or are not readable"""
    io_err_list = []
    conn_err_list = []
    for filename in netfilelist:
        try:
            netfile = h5py.File(filename, 'r')
            syn = numpy.asarray(netfile['/network/synapse'])
            netfile.close()
        except Exception, e:
            io_err_list.append(filename)
            continue
        conndict = defaultdict(int)
        for row in syn:
            conn = row[0] + '-' + row[1]
            conndict[conn] += 1
        if max(conndict.values()) > 2:
            conn_err_list.append(filename)
    return (io_err_list, conn_err_list)

def firstspike_time(tstart, train):
    t = np.nonzero(train > tstart)[0]
    if len(t > 0):
        return train[t[0]]
    return 1e15
        
def sort_spikestrains(cell_spike_train_dict, timepoint):
    cells = cell_spike_train_dict.keys()
    def sortkey(cell):
        train = cell_spike_train_dict[cell]
        return firstspike_time(timepoint, train)
    sorted_cells = sorted(cells, key=sortkey)
    return sorted_cells

def get_cell_index(cellstartindices, cellname):
    """cellstartindices - dict containing celltype and the starting
    index for this cell type in the whole population (cells of same
    type are contiguous ain the index space)."""
    celltype, index = cellname.split('_')
    return cellstartindices[celltype] + int(index)

def load_cell_graph(netfilepath):
    filehandle = h5py.File(netfilepath, 'r')
    syninfo = numpy.asarray(filehandle['/network/synapse'])
    cellinfo = numpy.asarray(filehandle['/runconfig/cellcount'])
    filehandle.close()
    # first extract the starting index of the celltypes in whole population
    cellstart = {}
    startindex = 0    
    for row in cellinfo:
        cellstart[row[0]] = startindex
        startindex += int(row[1])
    edges = defaultdict(set)
    for row in syninfo:
        src_name = row[0].partition('/')[0]        
        celltype, index_str, = src_name.split('_')
        src = cellstart[celltype] + int(index_str)
        dst_name = row[1].partition('/')[0]
        celltype, index_str, = dst_name.split('_')
        dst = cellstart[celltype] + int(index_str)
        edges[row[2]].add((src, dst))
    cellgraph = ig.Graph(0, directed=True)
    cellgraph.add_vertices(startindex)
    cellgraph.vs['name'] = ['%s_%d' % (celltype, index) for (celltype, count) in cellinfo for index in range(int(count))]
    celltypes = []
    for celltype, count in cellinfo:
        celltypes.extend([celltype] * int(count))
    cellgraph.vs['celltype'] = celltypes
    cellgraph.add_edges(edges['ampa'])
    cellgraph.add_edges(edges['gaba'])
    edge_types = []
    edge_types.extend(['ampa'] * len(edges['ampa']))
    edge_types.extend(['gaba'] * len(edges['gaba']))    
    cellgraph.es['synapse'] = edge_types
    return cellgraph

def read_networkgraph(filename):
    netfile = h5py.File(filename, 'r')
    syninfo = numpy.asarray(netfile['/network/synapse'])
    cellinfo = numpy.asarray(netfile['/runconfig/cellcount'])
    labels = []
    cellstartindices = {}
    current_start = 0
    for row in cellinfo:
        cellstartindices[row[0]] = current_start
        labels += ['%s_%d' % (row[0], ii) for ii in range(int(row[1]))]
        current_start += int(row[1])
    graph = ig.Graph(0, directed=True)
    graph.add_vertices(current_start)
    graph.vs['label'] = labels
    # Now add the edges
    edges = defaultdict(list)
    for row in syninfo:
        source = row[0].partition('/')[0]        
        dest = row[1].partition('/')[0]
        e1 = get_cell_index(cellstartindices, source)
        e2 = get_cell_index(cellstartindices, dest)
        edges[row[2]].append((e1, e2))
    ampa_edges = list(set(edges['ampa']))
    gaba_edges = list(set(edges['gaba']))
    
    graph.add_edges(ampa_edges + gaba_edges)    
    print len(graph.es)
    print len(ampa_edges), len(gaba_edges)
    labels = ['ampa'] * len(ampa_edges) + ['gaba'] * len(gaba_edges)
    print len(labels)
    graph.es['label'] = labels
    return graph
        
def get_files_with_same_settings(filelist, originalfile, hdfnodepath):
    """Look into the files in filelist and compare node hdfnodepath
    with that in originalfile. Return the names in filelist for which
    this node is identical."""
    for filename in filelist:
        pass

def get_files_with_same_cells(filelist, cellcount_dict):
    not_equal = []
    for filename  in filelist:
        f = h5py.File(filename, 'r')
        cellcounts = numpy.asarray(f['/runconfig/cellcount'])
        f.close()
        for row in cellcounts:
            if int(row[1]) != int(cellcount_dict[row[0]]):
                not_equal.append(filename)
                print filename, 'does not match', row[0], row[1], '!=', cellcount_dict[row[0]]
                break
    return list(set(filelist).difference(set(not_equal)))

def spike_probability_w_filter(srctrain, dsttrain, window):
    """Calculate in how many cases of spike in source cell, dest_cell
    fires first spike within time window"""
    if len(srctrain) == 0:
        return 0.0
    count = 0
    index = 0
    count = len(filter(lambda tspike: len(numpy.nonzero((dsttrain < tspike + window) & (dsttrain > tspike))[0]) > 0, srctrain))
    return float(count) / len(srctrain)

def get_spike_following_probability(srctrain, dsttrain, window):
    """Calculate in how many cases of spike in source cell, dest_cell
    fires first spike within time window"""
    if len(srctrain) == 0:
        return 0.0
    count = 0
    index = 0
    # ('SpinyStellate_231-SpinyStellate_22', 0.0)
    # ('SpinyStellate_231-SpinyStellate_22', 0.1428571492433548)
    # ('SpinyStellate_231-SpinyStellate_22', 0.2142857164144516)
    # ('SpinyStellate_231-SpinyStellate_22', 0.2142857164144516)
    # ('SpinyStellate_231-SpinyStellate_22', 0.3571428656578064)
    # ('SpinyStellate_231-SpinyStellate_22', 0.3571428656578064)
    for tspike in srctrain:
        if len(numpy.nonzero((dsttrain <= tspike + window) & (dsttrain > tspike))[0]) > 0:
            count += 1
    return float(count) / len(srctrain)

def find_spike_following_probability_in_connected_cells(netfilepath, datafilepath, timewindow):
    cellgraph = load_cell_graph(netfilepath)
    datafile = h5py.File(datafilepath, 'r')
    probabilities = {}
    for edge in cellgraph.es(synapse_eq='ampa'):
        src = cellgraph.vs[edge.source]['name']
        srctrain = numpy.asarray(datafile['/spikes'][src])
        dst = cellgraph.vs[edge.target]['name']
        dsttrain = numpy.asarray(datafile['/spikes'][dst])
        probabilities['%s-%s' % (src, dst)]  = get_spike_folloing_probability(srctrain, dsttrain, timewindow)
    datafile.close()
    return probabilities

def dump_spike_following_probabilities_in_connected_cells(netfilepathlist, datafilepathlist, timewindows):
    for netfilepath, datafilepath in zip(netfilepathlist, datafilepathlist):
        outfilename = datafilepath.replace('/data_', '/prob_')
        print 'Saving probabilities in', outfilename
        outfile = None
        try:            
            outfile = h5py.File(outfilename, 'w')
            grp = outfile.create_group('/spiking_prob')
            delta = timedelta(0,0,0)
            for ii in range(6):
                window = ii*1e-3
                start = datetime.now()
                probabilities = find_spike_following_probability_in_connected_cells(netfilepath, datafilepath, window)
                end = datetime.now()
                delta = delta + (end-start)
                data = numpy.asarray(probabilities.items(), dtype=('|S35,f'))
                print data[0]
                dset = grp.create_dataset('delta_%d' % (ii), data=data)
                dset.attrs['window'] = window       
            print 'Time to find probabilities:', (delta.seconds + delta.microseconds * 1e-6)
        finally:
            if outfile:
                outfile.close()

def find_spike_following_probability_in_unconnected_cells(netfile, datafile):
    cellgraph = load_cell_graph(netfilepath)
    

def dump_spike_following_probabilities_in_unconnected_cells(netfilepathlist, datafilepathlist, timewindows):
    """Compute the probability of a spike in a second cell following
    that in first cell when cells are not connected."""
    pass
        
def test():
    netfilepath = '/data/subha/cortical/py/data/2012_02_01/network_20120201_204744_29839.h5.new'
    datafilepath = '/data/subha/cortical/py/data/2012_02_01/data_20120201_204744_29839.h5'
    outfilename = datafilepath.rpartition('/')[-1].replace('data_', 'prob_')
    print 'Outfile', outfilename
    outfile = None
    try:
        outfile = h5py.File(outfilename, 'w')
        grp = outfile.create_group('/spiking_prob')
        delta = timedelta(0,0,0)
        for ii in range(6):
            window = ii*1e-3
            start = datetime.now()
            probabilities = find_probabilities(netfilepath, datafilepath, window)
            end = datetime.now()
            delta = delta + (end-start)
            data = numpy.asarray(probabilities.items(), dtype=('|S35,f'))
            print data[0]
            dset = grp.create_dataset('delta_%d' % (ii), data=data)
            dset.attrs['window'] = window       
        print 'Time to find probabilities:', (delta.seconds + delta.microseconds * 1e-6)
    finally:
        if outfile:
            outfile.close()

filenames = [
    "../py/data/2012_01_17/data_20120117_114805_6302.h5",
    "../py/data/2012_02_01/data_20120201_204744_29839.h5",
    "../py/data/2012_02_01/data_20120201_143411_29609.h5",
    "../py/data/2012_01_09/data_20120109_112852_22086.h5",
    "../py/data/2012_01_14/data_20120114_120027_996.h5",
    "../py/data/2012_01_03/data_20120103_101152_12049.h5",
    "../py/data/2012_01_03/data_20120103_100645_11976.h5",
    "../py/data/2012_01_11/data_20120111_135100_30693.h5",
    "../py/data/2012_01_11/data_20120111_135144_30762.h5",
    "../py/data/2012_01_23/data_20120123_092600_14963.h5",
    "../py/data/2012_01_23/data_20120123_092558_14940.h5",
    "../py/data/2012_01_23/data_20120123_092550_14913.h5",
    "../py/data/2012_01_23/data_20120123_092150_14871.h5",
    "../py/data/2012_02_03/data_20120203_144711_31441.h5",
    "../py/data/2012_02_03/data_20120203_144712_31468.h5",
    "../py/data/2012_02_03/data_20120203_144709_31418.h5",
    "../py/data/2012_01_18/data_20120118_142820_7865.h5",
    "../py/data/2012_01_13/data_20120113_170727_32728.h5",
    "../py/data/2012_02_06/data_20120206_112440_1220.h5",
    "../py/data/2012_02_06/data_20120206_112441_1248.h5",
    "../py/data/2012_01_19/data_20120119_201036_10692.h5",
    "../py/data/2012_01_19/data_20120119_132336_9035.h5",
    "../py/data/2012_01_29/data_20120129_175543_22839.h5",
    "../py/data/2012_01_29/data_20120129_175534_22710.h5",
    "../py/data/2012_01_29/data_20120129_175541_22810.h5",
    "../py/data/2012_01_29/data_20120129_175538_22760.h5",
    "../py/data/2012_01_29/data_20120129_175542_22835.h5",
    "../py/data/2012_01_29/data_20120129_175540_22787.h5",
    "../py/data/2012_01_29/data_20120129_115942_22585.h5",
    "../py/data/2012_01_29/data_20120129_175536_22733.h5",
    "../py/data/2012_01_10/data_20120110_115732_23924.h5",
    "../py/data/2012_01_25/data_20120125_131449_16448.h5",
    "../py/data/2012_01_25/data_20120125_131453_16471.h5",
    "../py/data/2012_01_25/data_20120125_131455_16498.h5",
    "../py/data/2012_01_25/data_20120125_131456_16525.h5"]

import sys

if __name__ == '__main__':
    # psth_multifile(filenames, ['SpinyStellate_0', 'DeepBasket_1', 'DeepLTS_2', 'DeepAxoaxonic_3', 'nRT_1', 'TCR_4'], 10e-3, combined=True, bg_interval=0.5, isi=0.125, pulse_width=2e-3)
    plot_psth_optimal_binsize(filenames, ['SpinyStellate', 'DeepBasket', 'DeepLTS', 'DeepAxoaxonic', 'nRT', 'TCR'], 1e-3, 100e-3, bg_interval=0.5, isi=0.125, pulse_width=2e-3)

# SpinyStellate optimal binsize: 0.499995553487 cost: 0.000346856234075 error: 0 no. of evaluations: 25
# DeepBasket optimal binsize: 0.194248984076 cost: 1.2071571773 error: 0 no. of evaluations: 24
# DeepLTS optimal binsize: 0.499995553487 cost: 0.000766664154798 error: 0 no. of evaluations: 25
# DeepAxoaxonic optimal binsize: 0.184999101659 cost: 0.325977767009 error: 0 no. of evaluations: 21
# nRT optimal binsize: 0.499995553487 cost: 0.00995474316129 error: 0 no. of evaluations: 25
# TCR optimal binsize: 0.499748242359 cost: 0.00450390170128 error: 0 no. of evaluations: 24
        
    # netfilename = sys.argv[1]
    # datafilename = sys.argv[2]
    # print 'Opening:', netfilename, 'and', datafilename
    # netfile = h5py.File(netfilename, 'r')
    # datafile = h5py.File(datafilename, 'r')
    # # stat = dump_synstat(netfile)
    # # probe_conn_set = find_spikes_by_stim(datafile,  netfile, 100e-3)
    # # for cellname in probe_conn_set:
    # #     print 'Probe connected:', cellname
    # bgset, probeset, = get_affected_cells(datafile, netfile, 100e-3)
    # print 'Only in probe set'
    # only_probe = probeset - bgset
    # for item in only_probe:
    #     print item
    # print 'The following are connected to a probed cell:'
    # connected = [cellname for cellname in only_probe if is_connected_to_probed_cell(netfile, cellname)]
    # for cellname in connected:
    #     print cellname
    # netfile.close()
    # datafile.close()

# 
# analyzer.py ends here

