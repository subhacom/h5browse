# scratch.py --- 
# 
# Filename: scratch.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Jun  6 11:13:39 2012 (+0530)
# Version: 
# Last-Updated: Wed Jun 27 17:53:19 2012 (+0530)
#           By: subha
#     Update #: 906
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# Go through specified files and associate spike counts with stimulus.
#
# Approach A:
#
# 1. Pick the stimulated cells.
# 2. Calculate the spike counts following bg, bg+probe.
# 3. See if there is a *systematic difference*
# Question: what is the systematic difference?

# Approach B:
#
# 1. Pick a random bunch of cells.
# 2. Calculate the spike counts following bg and bg+probe
# 3. Find out which cells show increased spike count due to addition of probe.
# 4. See if they are stimulated.

# In step 2, the measure can also be spike time.

# I feel approach B is less biased than A.

# Change log:
# 
# 
# 
# 

# Code:

import os
import random
import h5py as h5
import numpy as np
from collections import defaultdict
from matplotlib import pyplot as plt

import analyzer

def find_data_with_stimulus(filenamelist):
    """Open files passed in `filenamelist` and check for background
    and probe stimulus data. The files must be data files, not network
    files. Return a list of open file handles of those that are
    good"""
    files_with_stim = []
    files_to_close = []
    for filename in filenamelist:
        try:
            fh = h5.File(filename, 'r')
        except IOError:
            print filename, 'could not be opened'
            continue
        try:
            bgtimes = analyzer.get_bgtimes(fh)
            probetimes = analyzer.get_probetimes(fh)
            if (0 in bgtimes.shape) or (0 in probetimes.shape):
                files_to_close.append(fh)
            else:
                files_with_stim.append(fh)
        except KeyError:
            print filename, 'does not have stimulus data'
            files_to_close.append(fh)
    for fh in files_to_close:
        print 'File without stimulus info:', fh.filename
        fh.close()
    return files_with_stim

def categorise_networks(filehandles):
    """Categorize the files based on cellcount and network generation
    rng seed. filehandles should be a list of data files.

    Returns a dict whose keys are seeds and values are list of
    filehandles that used that seed.

    """
    seeds = defaultdict(dict)
    for fh in filehandles:
        try:
            numinfo = dict(fh['runconfig/numeric'])
            cellcount = dict(fh['runconfig/cellcount'])        
        except KeyError, e:
            print fh.filename, 'does not have a key', e
            continue
        # Here we combine the seed and the hash of the entries in
        # cellcount map to create a unique key.
        # The hash is computed from the string
        # 'key1,key2,...,keyN:val1,val2,...,valN'
        sorted_keys = sorted(cellcount.keys())
        sorted_values = [cellcount[key] for key in sorted_keys]
        cellcountinfo = ','.join(sorted_keys)+':'+','.join(sorted_values)
        directory = os.path.dirname(fh.filename)
        filename = os.path.basename(fh.filename)
        if filename.startswith('data_'):
            netfilename = filename.replace('data_', 'network_').replace('.h5', '.h5.new')
            netfile = h5.File(os.path.join(directory, netfilename), 'r')
            try:
                stim_conn = dict(netfile['/stimulus/connection'])
                netfile.close()
                sorted_keys = sorted(stim_conn.keys())
                stiminfo = ','.join(sorted_keys) + ':' + \
                    ','.join([stim_conn[key] for key in sorted_keys])
            except KeyError:
                print netfilename, ' - has no stimulus connection information.'
                netfile.close()
                continue                                    
        k = None
        if 'rngseed' in numinfo:
            k = numinfo['rngseed']
        else:
            k = numinfo['numpy_rngseed']
        d = seeds[k]        
        nethash = hash(cellcountinfo + '.' + stiminfo)
        if nethash not in d:
            d[nethash] = [fh]
        else:
            d[nethash].append(fh)
    print '--------- Catgorise network ---------'
    for key, value in seeds.items():
        for nethash, fh in value.items():
            for f in fh:
                print 'k"%s" #"%d" f"%s"' % (key, nethash, f.filename)
    print '----- end catgorise networks --------'
    return seeds        

def compare_synapses(filehandles):
    raise NotImplementedError('Synapse-by-synapse comparison is yet to be implemented')    
    
def compare_networks(filehandles, paranoid=False):
    """Compare a set of network files for identity, taking the first
    as the left side and comparing all the others to it."""
    # First check if the specified files represent the same network.
    if paranoid:
        return compare_synapses(filehandles)
    seed = None
    cellcount = None
    for fh in filehandles:
        try:
            numeric_info = dict(fh['runconfig/numeric'])
            if 'rngseed' in numeric_info:
                new_seed = numeric_info['rngseed']
            else:
                new_seed = numeric_info['numpy_rngseed']
            new_cellcount = dict(fh['runconfig/cellcount'])            
            if seed is None:
                seed = new_seed
                cellcount = new_cellcount
                continue
            if seed != new_seed:
                print 'File has a different numpy rng seed:', fh.filename
                return False
            for key, value in cellcount.items():
                if key not in new_cellcount:
                    print 'Celltype `', key, '` not in file `', fh.filename, '`'
                    return False
                if value != new_cellcount[key]:
                    print 'Celltype `', key, '` has different value in file `', fh.filename, '`'
                    return False            
        except KeyError, e:
            print fh.filename, 'does not have some of the standard information'
            print e
            return False
    return True

def pick_cells(filehandles, celltype, number, paranoid=False):
    """Select `number` cells of `celltype` type from all files listed
    in `filenames`.

    The files should represent the same network model. This can be
    quickly determined by checking the seed for numpy rng stored in
    the files runconfig group. If paranoid is set to True, then files
    are checked synapse by synapse for identity.

    filenames : list
    files which have the same network model. This is determined by the
    numpy random number generated seed.

    celltype: str
    cell class name, e.g. SpinyStellate

    number: int
    number of cells to pick up
    
    """
    if not compare_networks(filehandles, paranoid) or len(filehandles) == 0:
        return None
    cellcount = dict(filehandles[0]['runconfig/cellcount'])
    count = int(cellcount[celltype])
    if count < number:
        number=count
    indices = random.sample(range(count), number)
    return ['%s_%d' % (celltype, index) for index in indices]

def get_stim_aligned_spike_times(fhandles, cellnames):
    """Collect the spike times for each cell from all the files with
    respect to the stimuli.

    Parameteres
    -----------

    fhandles: list
    open data file handles.

    cellnames: list
    list of cell names to be checked.

    Returns
    -------
    
    A pair containing dicts of list of arrays of spike times following
    each stimulus presentation: one for background alone and one for
    background + probe. All the spike times are with respect to the
    preceding stimulus.
    """
    plot = 'all'
    bg_spikes = defaultdict(list)
    probe_spikes = defaultdict(list)
    for fh in fhandles:
        stiminfo = dict(fh['runconfig/stimulus'][:])
        simtime = float(dict(fh['runconfig/scheduling'])['simtime'])        
        stim_onset = float(stiminfo['onset'])
        interval = float(stiminfo['bg_interval'])
        stimwidth = float(stiminfo['pulse_width'])
        spike_times = get_spike_times(fh, cellnames)
        bgtimes = analyzer.get_bgtimes(fh)
        probetimes = analyzer.get_probetimes(fh)
        print 'Background times', bgtimes
        print 'Probe times', probetimes
        bgbins = [(bgtimes[ii], bgtimes[ii]+interval+stimwidth) for ii in range(0, len(bgtimes), 2)]
        print bgbins
        probebins = [(pt, pt+interval+stimwidth) for pt in probetimes]
        print probebins
        # Probe stimulus is designed to align with every alternet bg
        # stmulus.
        cell_no = 1
        for cell, spikes in spike_times.items():
            bg = [spikes[(spikes >= bin[0]) & (spikes < bin[1])]
                  for bin in bgbins]
            bg_spikes[cell] += bg
            probe = [spikes[(spikes >= bin[0]) & (spikes < (bin[1]))]
                     for bin in probebins]
            probe_spikes[cell] += probe
            for x in bg:
                print 'bg', x
            for x in probe:
                print 'probe', x
            if plot is not None:
                x = np.concatenate(bg)
                plt.plot(x, np.ones(len(x))*cell_no, 'bx')
                x = np.concatenate(probe)
                plt.plot(x, np.ones(len(x))*cell_no, 'r+')
            if plot == 'each':
                plt.title('%s: %s' % (fh.filename, cell))
                plt.show()
            elif plot == 'all':
                cell_no += 1
        if plot == 'all':
            plt.title(fh.filename)
            plt.show()
    return (bg_spikes, probe_spikes)

def get_spike_times(filehandle, cellnames):
    """Return a dict of cellname, spiketime list for all cells in
    `cellnames`."""
    ret = {}
    for cell in cellnames:
        ret[cell] = filehandle['spikes/%s' % (cell)][:]
    return ret

def get_square_wave_edges(filehandle, path):
    """Return a list of times of the leading edges of a square
    wave. Used for extracting stimulus times."""
    series = filehandle[path][:]
    simtime = float(dict(filehandle['runconfig/scheduling'][:])['simtime'])
    dt = simtime / len(series)
    return np.nonzero(np.diff(series) > 0.0)[0] * dt

def get_t_first_spike(spiketimes_list, default):
    ret = []
    for st in spiketimes_list:
        if len(st) > 0:
            ret.append(st[0])
        else:
            ret.append(default) # a placeholder value for when there was no spike    
    return np.array(ret)

def get_spike_freq(spiketimes_list, delay=0.0, window=50e-3):
    """Get the average spike rate within a period `window` after
    `delay` time from stimulus onset."""
    ret = []
    for st in spiketimes_list:
        spikes = len(np.nonzero((st > delay) & (st < delay+window))[0])
        ret.append(spikes * 1.0 / window)
    return np.array(ret)

def get_max_spike_count(spike_time_list, window=10e-3):
    """Get the maximum frequency using a sliding window of width `window`.

    Parameters
    ----------
    
    spike_time_list: list of arrays containing spike times. 

    app specific note: When background and probe stimulus alternate,
    the spikes following each stimulus are collected in an
    array. Arrays from multiple stimulus application constitute
    spike_time_list.

    window:  the width of the time window in which to maximize the number of spikes

    

    Returns 
    -------

    the position of the centre of the window and the number of
    spikes within the window for each array in `spike_time_list`.
    
    """
    ret = []
    for spikes in spike_time_list:
        max_count = 0
        max_time = 0
        for spike in spikes:
            count = len(np.nonzero((spikes <= spike) & (spikes > (spike - window)))[0])
            if count > max_count: 
                max_count = count
                max_time = spike - window / 2.0
        ret.append((max_time, max_count / window))
    return np.array(ret)

def get_probed_cells(filehandle, hop=1):
    ret = []
    dirname = os.path.dirname(filehandle.filename)
    fname = os.path.basename(filehandle.filename)
    if fname.startswith('data'):
        fname = fname.replace('data_', 'network_').replace('.h5', '.h5.new')
    netfilename = os.path.join(dirname, fname)
    print 'Network file:', netfilename
    netfile = h5.File(netfilename, 'r')
    try:
        stim_dests = netfile['stimulus/connection'][:]
    except KeyError:
        print 'No stimulus in file', filehandle.filename
        return ret
    probe_dests = [row[1] for row in stim_dests if row[0].endswith('stim_probe')]
    if not probe_dests:
        print 'No probed cells in this file:', filehandle.filename
        netfile.close()
        return ret
    probe_dests = np.char.split(probe_dests, '/')
    probe_dests = [token[-2] for token in probe_dests]
    try:
        sources = netfile['/network/synapse']['source']
        dests = netfile['/network/synapse']['dest']
    except KeyError:
        print netfile.filename, 'missing synapse information'
        netfile.close()
        return ret
    sources = [row[0] for row in np.char.split(sources, '/')]
    dests = [row[0] for row in np.char.split(dests, '/')]
    ret = set([dests[ii] for ii in range(len(sources)) if sources[ii] in probe_dests])
    netfile.close()
    return ret

def collect_statistics(datafiles, celltypes):
    """Collect some statistics for cells of type listed in `celltypes`
    from `datafiles`

    Returns
    -------
    
    A pair of dictionaries, (bginfo, probeinfo) which contain the data
    for background only stimulus and data for background+probe
    stimulus.

    Each dict is keyed with cell name and the values are dicts themselves. 
    The values contain 

    t_first_spike - array of time to first spike after each stimulus.
    f_avg - array of average spiking rate after each stimulus
    f_peak_spiking - the peak spiking rate within a window (20 ms default).
    t_peak_spiking - window position for peak spiking above.
    """
    if len(datafiles) == 0:
        return None
    cellcount = dict(datafiles[0]['/runconfig/cellcount'])
    stimulus_interval = float(dict(datafiles[0]['/runconfig/stimulus'])['bg_interval'])
    print '****************************************'
    print '* File names:'
    for fh in datafiles:
        print '*', fh.filename
    print '* --------------------------------------'
    print '* Cell count:'
    for cell, count in cellcount.items():
        if int(count) > 0:
            print '*', cell, ':', count
    probed_cells = get_probed_cells(datafiles[0])
    probe_info = defaultdict(dict)
    bg_info = defaultdict(dict)
    width = 20e-3
    for celltype in celltypes:
        cells = pick_cells(datafiles, celltype, 100000) # choose all cells (assuming <= 1000 cells of each type)
        if not cells:
            print '!! No entry for celltype', celltype
            continue
        bgtimes, probetimes, = get_stim_aligned_spike_times(datafiles, cells)
        for cell in cells:
            tfs = [v[0] if len(v) > 0 else stimulus_interval for v in bgtimes[cell]]
            bg_info[cell]['t_first_spike'] = tfs
            # print cell, 'bgtimes:', bgtimes[cell]
            bg_info[cell]['f_avg'] = np.array([len(st) for st in bgtimes[cell]]) / stimulus_interval
            peak_spiking_info = get_max_spike_count(bgtimes[cell], width)
            if len(peak_spiking_info) == 0:
                peak_spiking_info = - np.ones((1,2))
            bg_info[cell]['t_peak_spiking'] = peak_spiking_info[:,0]
            bg_info[cell]['f_peak_spiking'] = peak_spiking_info[:,1]
            probe_info[cell]['t_first_spike'] = [v[0] if len(v) > 0 else stimulus_interval for v in probetimes[cell]]
            # print cell, 'probetimes:', probetimes[cell]          
            probe_info[cell]['f_avg'] = np.array([len(spiketimes) for spiketimes in probetimes[cell]]) / stimulus_interval
            peak_spiking_info = get_max_spike_count(probetimes[cell], width)
            if len(peak_spiking_info) == 0:
                peak_spiking_info = - np.ones((1,2))
            probe_info[cell]['t_peak_spiking'] = peak_spiking_info[:, 0]
            probe_info[cell]['f_peak_spiking'] = peak_spiking_info[:, 1]
                
            # print bg_info[cell]
    return (bg_info, probe_info)
            
import subprocess

def get_valid_files_handles(directory):
    # Files smaller than 1 MB will not have any usefule data for analysis
    pipe = subprocess.Popen(['find', directory, '-type', 'f', '-name', 'data*.h5', '-size','+1M'], stdout=subprocess.PIPE)
    # TODO use subprocess.communicate to avoid issues with large amount of output
    files = [line.strip() for line in pipe.stdout]
    return find_data_with_stimulus(files)
    


import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'Usage:', sys.argv[0], 'filelist celltype number outputfileprefix'
        print 'Retrieve the stimulus aligned spike times from filenames listed in `filelist` file.'
        sys.exit(0)
    
    filelistfile = sys.argv[1]
    celltype = sys.argv[2]
    number = int(sys.argv[3])
    ofprefix = sys.argv[4]
    fhandles = []
    with open(sys.argv[1], 'r') as filelist:
        for filename in filelist:
            try:
                fhandles.append(h5.File(filename.strip(), 'r'))
            except IOError, e:
                print e
    cellnames = pick_cells(fhandles, celltype, number)
    print 'Cells:'
    print cellnames
    (bg_spikes, probe_spikes) = get_stim_aligned_spike_times(fhandles, cellnames)
    print 'BG data'
    print bg_spikes
    print 'PROBE DATA'
    print probe_spikes
    # bg_file = h5.File('%s_bg.h5' % (ofprefix), 'w')
    # datagrp = bg_file.create_group('data')
    # datagrp.attrs['note'] = 'Spike times following only-background stimulus'
    # for cellname, spiketimes in bg_spikes.items():
    #     ds = datagrp.create_dataset(cellname, data=np.array(spiketimes).ravel())
    # bg_file.close()
    # probe_file = h5.File('%s_probe.h5' % (ofprefix), 'w')
    # datagrp = probe_file.create_group('data')
    # datagrp.attrs['note'] = 'Spike times following probe+background stimulus'
    # for cellname, spiketimes in probe_spikes.items():
    #     ds = datagrp.create_dataset(cellname)
    #     ds[:] = spiketimes
    # probe_file.close()

    
# 
# scratch.py ends here
