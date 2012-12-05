#!/usr/bin/env python
# analyze_nonbursting.py --- 
# 
# Filename: analyze_nonbursting.py
# Description: 
# Author: 
# Maintainer: 
# Created: Tue Dec  4 16:40:12 2012 (+0530)
# Version: 
# Last-Updated: Wed Dec  5 10:19:35 2012 (+0530)
#           By: subha
#     Update #: 131
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# analyze (possibly using principal components) spiny stellate cells
# that are not bursting.
# 
# The datafiles and the cells that match criterion are in the file
# nonbursting_spinystellates.txt. and
# nonbursting_spinystellate_frac.txt - which has fraction of spiny
# stellate cells that do not burst in each data file.

# Change log:
# 
# 
# 

# Code:

import h5py as h5
import os
print os.getcwd()
from datetime import datetime
from get_files_by_ts import *
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt
from matplotlib._pylab_helpers import Gcf
import random
from traubdata import TraubData
import analyzer

def load_nonbursting_spinystellate_cell_file(fromfile='nonbursting_spinystellates.txt'):
    filename_cell_map = defaultdict(set)
    cell_filename_map = defaultdict(set)
    with open(fromfile) as flistfile:
        for line in flistfile:
            stripped = line.strip()
            if (not stripped) or stripped.startswith('#'):
                continue
            tokens = [t.strip() for t in stripped.split(',')]
            filename_cell_map[tokens[0]].add(tokens[1])
            cell_filename_map[tokens[1]].add(tokens[0])
    return (filename_cell_map, cell_filename_map)

def load_nonbursting_spinystellate_frac_file(fromfile='nonbursting_spinystellate_frac.txt'):
    filename_frac_map = defaultdict(list)
    with open(fromfile) as flistfile:
        for line in flistfile:
            stripped = line.strip()
            if (not stripped) or stripped.startswith('#'):
                continue
            tokens = [t.strip() for t in stripped.split(',')]
            filename_frac_map[tokens[0]].append(float(tokens[1]))
    return filename_frac_map
    
def plot_synaptic_conductances(cell_filename_map, filename_data_map):
    """Plot the excitatory and inhibitory conductances for all cells
    for which the synaptic conductance information is available
    (practically 'SpinyStellate_0' in most recent simulations). 

    cell_filename_map: dict mapping cellnames to filenames.

    filename_data_map: dict mapping filenames to TraubData objects.

    """
    rows = 4
    all_rows = len(cell_filename_map['SpinyStellate_0'])    
    fig = None
    axno = 0
    filenames = sorted(cell_filename_map['SpinyStellate_0'])
    for filename in filenames:
        data = filename_data_map[filename]
        if not 'synapse' in data.fdata:
            print 'No synaptic conductance in', data.fdata.filename
            continue
        gE = np.sum([np.asarray(data.fdata['synapse'][gsyn]) for gsyn in data.fdata['synapse'] if ('ampa' in gsyn) or ('nmda' in gsyn)],
                         axis=0)
        gI = np.sum([np.asarray(data.fdata['synapse'][gsyn]) for gsyn in data.fdata['synapse'] if 'gaba' in gsyn],
                         axis=0)
        ts = np.linspace(0, data.simtime, len(gE))
        if axno % rows == 0:
            plt.show()
            # This is to save on memory
            if fig:
                plt.close(fig)
            fig = plt.figure(axno/rows)
        ax = fig.add_subplot(rows, 1, axno%rows+1)
        ax.set_title(filename)
        ax.set_ylabel('Conductance (nS)')
        cellcounts = '\n'.join(['%s:%d' % item for item in data.cellcounts._asdict().items()])
        ax.text(2, 5, cellcounts, ha='left')
        ax.plot(ts, gE*1e9, 'r-', alpha=0.7)
        ax.plot(ts, gI*1e9, 'b-', alpha=0.3)
        ts = np.linspace(0, data.simtime, len(data.bg_stimulus))
        bgtimes = ts[np.diff(data.bg_stimulus) > 0]
        ax.plot(bgtimes, np.ones(len(bgtimes)), 'g^', alpha=0.5)
        axno += 1

if __name__ == '__main__':
    filename_cell_map, cell_filename_map = load_nonbursting_spinystellate_cell_file()
    filename_data_map = dict([(filename, TraubData(filename)) for filename in filename_cell_map.keys()])
    plot_synaptic_conductances(cell_filename_map, filename_data_map)
    plt.show()


# 
# analyze_nonbursting.py ends here
