# scratch.py --- 
# 
# Filename: scratch.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Jun  6 11:13:39 2012 (+0530)
# Version: 
# Last-Updated: Thu Jun  7 16:29:46 2012 (+0530)
#           By: subha
#     Update #: 390
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

import random
import h5py as h5
import numpy as np
from collections import defaultdict

def find_data_with_stimulus(filenamelist):
    files_with_stim = []
    for filename in filenamelist:
        try:
            fh = h5.File(filename, 'r')
        except IOError:
            print filename, 'could not be opened'
            continue
        if ('runconfig' in fh.keys()) and ('stimulus' in fh['runconfig'].keys()):
            files_with_stim.append(filename)
        fh.close()
    return files_with_stim

def categorise_networks(filehandles):
    """Categorize the files based on cellcount and network
    generation rng seed"""
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
        cchash = hash(','.join(cellcount.keys())+':'+','.join(cellcount.values()))
        k = None
        if 'rngseed' in numinfo:
            k = numinfo['rngseed']
        else:
            k = numinfo['numpy_rngseed']
        d = seeds[k]        
        if cchash not in d:
            d[cchash] = [fh]
        else:
            d[cchash].append(fh)
    for key, value in seeds.items():
        for cchash, fh in value.items():
            for f in fh:
                print 'k"%s" #"%d" f"%s"' % (key, cchash, f.filename)
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
    
    A pair containing dicts of spike times: one for backe ground alone
    and one for background + probe. All the spike times are with
    respect to the preceding stimulus.
    """
    bg_spikes = defaultdict(list)
    probe_spikes = defaultdict(list)
    for fh in fhandles:
        spike_times = get_spike_times(fh, cellnames)
        simtime = float(dict(fh['runconfig/scheduling'][:])['simtime'])
        stiminfo = dict(fh['runconfig/stimulus'][:])
        stim_onset = float(stiminfo['onset'])
        # Probe stimulus is designed to align with every alternet bg
        # stmulus.
        interval = float(stiminfo['bg_interval'])
        for cell, spikes in spike_times.items():
            bg_spikes[cell] = np.r_[bg_spikes[cell], spikes[spikes > (stim_onset + interval)] % (2*interval)]
            probe_spikes[cell] = np.r_[probe_spikes[cell], spikes[spikes > (stim_onset + 2 * interval)] % (2 * interval)]
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
    (bg_spikes, probe_spikes) = get_stim_aligned_spike_times(fhandles, cellnames)
    bg_file = h5.File('%s_bg.h5' % (ofprefix), 'w')
    datagrp = bg_file.create_group('data')
    datagrp.attrs['note'] = 'Spike times following only-background stimulus'
    for cellname, spiketimes in bg_spikes.items():
        ds = data.create_dataset(cellname)
        ds[:] = spiketimes
    bg_file.close()
    probe_file = h5.File('%s_probe.h5' % (ofprefix), 'w')
    datagrp = probe_file.create_group('data')
    datagrp.attrs['note'] = 'Spike times following probe+background stimulus'
    for cellname, spiketimes in probe_spikes.items():
        ds = data.create_dataset(cellname)
        ds[:] = spiketimes
    probe_file.close()

    
# 
# scratch.py ends here
