# analyze_excitation_inhibition_balance.py --- 
# 
# Filename: analyze_excitation_inhibition_balance.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Nov 14 12:36:04 2012 (+0530)
# Version: 
# Last-Updated: Sat Nov 17 19:16:40 2012 (+0530)
#           By: subha
#     Update #: 399
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# This is for analyzing the excitation inhibition balance
# 
# 

# Change log:
# 
# 
# 
# 

# Code:

import sys
import h5py as h5
import os
import subprocess
from datetime import datetime
from operator import itemgetter
from get_files_by_ts import *
import numpy as np
from matplotlib import pyplot as plt
from matplotlib._pylab_helpers import Gcf
import random

def close_all_figures():
    current_figures = [fig_manager.canvas.figure for fig_manager in Gcf.get_all_fig_managers()]
    for fig in current_figures:
        fig.close()

def invert_container_map(container_map):
    """Get the inverse map of container_map, container_map:
    defaultdict(some_container_type)

    Returns a dict mapping each entry of the containers (values) to
    the key corresponding to the container object

    """
    return {v:k 
            for k, vlist in container_map.items() 
            for v in vlist}

def randomized_plot(file_stub_map, plot_function):
    pass

def plot_spike_rasters(cells, data, colordict):
    """Plot spike raster of cells from `cells` list using data in
    `data` list.

    `cells` and `data` must be of same length. data[i] contains spike
    times for cells[i].

    `colordict` dictionary contains the mapping from celltype to plot
    color.
    
    """
    for index, (cell, spiketimes) in enumerate(zip(cells, data)):
        plt.plot(spiketimes, np.ones(len(spiketimes)) * index, 
                 color=colordict[cell.split('_')[0]],
                 ls='',
                 marker=',', 
                 mew=0)
        
def classify_cells(cells):
    """Return a dict maping celltype to list of cells."""
    categories = defaultdict(list)
    for cell in cells:
        celltype = cell.split('_')[0]
        categories[celltype].append(cell)
    return categories

def randomized_spike_rasters_allcelltype(category_map, data_map, cellcounts, colordict):
    """Display spike rasters for all cell types with randomized
    labels.

    category_map: map from cellcounts to data file paths with that count

    data_map: map from file paths to {cellname: spike train} dict

    cellcounts: cellcount_tuple specifying number of cells to plot for each cell type

    colordict: map from celltype to color-string for the plot color

    """
    cellcounts = cellcounts._asdict()
    file_category_map = invert_container_map(category_map)
    files = file_category_map.keys()
    random.shuffle(files)
    stim_data = load_stim_data(files)
    simtimes = get_simtime(files)
    file_figtitle_map = {}
    file_fig_map = {}    
    for figindex, fname in enumerate(files):
        fig = plt.figure(figindex+1)
        file_fig_map[fname] = fig
        file_figtitle_map[fname] = figindex + 1
        fdata = data_map[fname]
        cc = defaultdict(list) # dict from cell type to cells
        cells = sorted(fdata.keys())                
        celltype_cell_map = classify_cells(cells)
        cells_to_plot = []
        for celltype, cells in celltype_cell_map.items():
            cells_to_plot += cells[:cellcounts[celltype]]
        data_to_plot = [fdata[cell] for cell in cells_to_plot]
        plot_spike_rasters(cells_to_plot, data_to_plot, colordict)
        plt.plot(np.linspace(0, simtimes[fname], len(stim_data[fname][0])), stim_data[fname][0]*1e9*len(cells_to_plot), alpha=0.2)
    with open('filetofigure_%s.csv' % 
              (datetime.now().strftime('%Y%m%d_%H%M%S')), 'w') as fd:        
        fd.write('filename, figure, %s\n' % (', '.join(cellcount_tuple._fields)))
        for cc, files in category_map.items():
            for x in cc:
                print x
                print str(x)
            counts = ', '.join([str(c) for c in cc])
            print counts
            for fname in files:
                fd.write('%s, %d, %s\n' % (fname, file_figtitle_map[fname], counts))
    plt.show()
    for filename, figure in file_fig_map.items():
        figure.set_size_inches(4, 3)
        figfile = os.path.basename(filename)+'.png'
        figure.savefig(figfile)
        print 'Saved', figfile
        
if __name__ == '__main__':    
    filenames = find_files('/data/subha/rsync_ghevar_cortical_data_clone', '-iname', 'data_*.h5') # Find all data files in the directory
    current_fts = get_fname_timestamps(filenames, '20120918', '20121201') # These simulations were done from 2012-09-19 till 2012-11-??
    # We'll store the file (descriptor, timestamp)  in fdts
    fdts = []
    notes = get_notes_from_files(current_fts.keys())
    print '=== printing filenames and notes ==='
    for k, v in notes.items():
        print '^', k, v
    print '---'
    categories = classify_files_by_cellcount(current_fts.keys())
    # After categorising the good files, we work with only those files
    # with 240 spiny stellate cells (others test simulations)
    goodfiles = {cc: files for cc, files in categories.items() if cc.SpinyStellate == 240}
    data = {}
    for cc, fnames in goodfiles.items():        
        data.update(load_spike_data(fnames))
    print 'Loaded data from', len(data), 'files'
    colordict = load_celltype_colors()
    cellcounts=cellcount_tuple(SupPyrRS=0,
                               SupPyrFRB=0,
                               SupBasket=0,
                               SupAxoaxonic=0,
                               SupLTS=0,
                               SpinyStellate=240,
                               TuftedIB=0,
                               TuftedRS=0,
                               DeepBasket=0,
                               DeepAxoaxonic=0,
                               DeepLTS=0,
                               NontuftedRS=0,
                               TCR=100,
                               nRT=0)
    randomized_spike_rasters_allcelltype(goodfiles, data, cellcounts, colordict)
        
                
# 
# analyze_excitation_inhibition_balance.py ends here
