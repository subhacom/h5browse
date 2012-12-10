# analyze_excitation_inhibition_balance.py --- 
# 
# Filename: analyze_excitation_inhibition_balance.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Nov 14 12:36:04 2012 (+0530)
# Version: 
# Last-Updated: Mon Dec 10 22:19:58 2012 (+0530)
#           By: subha
#     Update #: 1191
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

import analyzer

params = {'font.size' : 12,
          'axes.labelsize' : 12,
          'axes.linewidth': 2,
          'font.size' : 12,
          'text.fontsize' : 12,
          'legend.fontsize': 12,
          'xtick.labelsize' : 12,
          'ytick.labelsize' : 12,
}
plt.rcParams.update(params)


from traubdata import TraubData, cellcount_tuple

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

def plot_spinstell_sync_spike_with_num_deepbasket(cutoff):
    filenames = []
    with open('exc_inh_files.txt', 'r') as filelist:
        for line in filelist:
            filename = line.strip()
            if filename:
                filenames.append(filename)
    DeepBasket_count_data_map = defaultdict(list)
    for filename in filenames:
        print 'Opening', filename
        data = TraubData(filename)
        DeepBasket_count_data_map[data.cellcounts.DeepBasket].append(data)
    DeepBasket_count_data_map_hist_map = {}
    # For each deepbasket count we store a list of synchronized
    # spiking info. Each list entry corresponds to one data file and
    # is a list of bin-center from that datafile.    
    syncspike_times_dict = defaultdict(list)
    bins = np.arange(0, 20.005, 5e-3)
    for deepbasket_count, datalist in DeepBasket_count_data_map.items():        
        syncspike_times = get_population_spike_times(datalist, 
                                                'SpinyStellate', 
                                                cutoff, 
                                                (0.0, 20.0))
        syncspike_times_dict[deepbasket_count] = syncspike_times
    data_dict = {}
    for deepbasket_count, syncspike_times_list in syncspike_times_dict.items():
        print '^', deepbasket_count
        mean_period_list = np.zeros(len(syncspike_times_list))
        for ii, sst_list in enumerate(syncspike_times_list):
            print '!', type(sst_list[0])
            sst = np.array(sst_list)            
            mean_period_list[ii] = np.mean(np.diff(sst))
        mean_period = np.mean(mean_period_list)
        std = np.std(mean_period_list)
        data_dict[deepbasket_count] = (mean_period, std)
    counts = sorted(data_dict.keys())
    err = [data_dict[key][1] for key in counts]
    mean = [data_dict[key][0] for key in counts]
    left = np.array(counts) - 0.4
    fig = plt.figure()
    ax = fig.add_subplot(111)
    rects = ax.bar(left, mean, color='#8A8A8A', ec='none', yerr=err, ecolor='k')
    ax.set_xticks(sorted(syncspike_times_dict.keys()))
    ax.set_xlabel('No. of Deep Basket Cells')
    ax.set_ylabel('Mean period (s)')
    # Fill this if it is going to be part of a panel
    # fig.suptitle('')    
    # This will put the heights of each bar on top of it - clutters the plot
    # for rect in rects:
    #     height = rect.get_height()
    #     ax.text(rect.get_x()+rect.get_width()/2., 1.05*height, '%0.2f'% (height),
    #             ha='center', va='bottom')
    fig.patch.set_facecolor('white')
    pdf = PdfPages('periodicitywithdeepbasketcount.pdf')
    pdf.savefig()
    pdf.close()
    
def get_population_spike_times(datalist, celltype, cutoff, timerange):
    """Retrieve the population spike times where the fraction of cells
    spiking within a bin is more than cutoff. NOTE: this is not exact
    as the same cell may spike twice within a bin. By setting binsize
    to 5 ms we expect to avoid that (unless there is a burst)"""    
    syncspike_times = []
    tstart = 0
    if timerange[0] > 0:
        tstart = timerange[0]
    for data in datalist:
        if timerange[1] > data.simtime:
            tend = data.simtime
        else:
            tend = timerange[1]
        bins = np.arange(tstart, tend+5e-3, 5e-3)
        spiketrain = get_population_spikes(data, celltype)
        nums, bins = np.histogram(spiketrain, bins, 
                                       weights=np.ones(len(spiketrain))/data.cellcounts._asdict()[celltype])
        n_bin_list = []
        for _n, _bincenter in zip(nums, (bins[0:-1]+bins[1:])/2.0):
            if _n > cutoff:
                n_bin_list.append(_bincenter)
        syncspike_times.append(n_bin_list)
    return syncspike_times

def get_population_spikes(data, celltype, timerange=(0, 1e9)):
    """Retrieve the spiketimes from TraubData object `data` for members of
    `celltype` in a single array."""
    spiketimes = []
    for cell, spikenode in data.spikes.items():
        ctype = cell.split('_')[0]
        if ctype != celltype:
            continue
        spiketrain = np.asarray(spikenode)
        spiketrain = spiketrain[(spiketrain >= timerange[0]) & 
                           (spiketrain < timerange[1])]
        if len(spiketrain) > 0:
            spiketimes.append(spiketrain)
    return np.concatenate(spiketimes)

def get_spiking_cell_counts(data, celltype, timerange=(0,1e9), binsize=5e-3):
    tstart = 0
    if timerange[0] > 0:
        tstart = timerange[0]
    tend = data.simtime
    if timerange[1] < tend:
        tend = timerange[1]
    bins = np.arange(tstart, tend+binsize, binsize)
    binned_cells = []
    for cell, spikenode in data.spikes.items():
        ctype = cell.split('_')[0]
        if ctype != celltype:
            continue
        spiketrain = np.asarray(spikenode)
        spiketrain = spiketrain[(spiketrain >= timerange[0]) &
                                (spiketrain < timerange[1])]
        if len(spiketrain) > 0:
            hist = np.histogram(spiketrain, bins)
            spiked = np.where(hist[0] > 0, 1.0, 0.0)
            binned_cells.append(spiked)
    return np.sum(binned_cells, axis=0)
    
def plot_population_spike_histogram(trbdatalist, timerange, bins, colordict):
    """Plot histogram of spike counts for different celltypes.
    
    trbdatalist: list TraubData objects wrapping the data files

    timerange: 2-tuple time window to consider for the histogram

    bins: bin positions for histogram

    colordict: celltype-color dictionary
    """
    figures = []    
    for data in trbdatalist:
        figure = plt.figure(data.fdata.filename)
        figure.suptitle(data.fdata.filename)
        figures.append(figure)
        celltype_spiketrain_map = defaultdict(list)
        for cell, spikenode in data.spikes.items():
            celltype = cell.split('_')[0]
            # Ignore ectopic spikes and incorrect celltype names
            if celltype not in cellcount_tuple._fields:
                continue
            spiketrain = np.asarray(spikenode)
            chunk = spiketrain[(spiketrain >= timerange[0]) & 
                               (spiketrain < timerange[1])]
            if len(chunk) > 0:
                celltype_spiketrain_map[celltype].append(chunk)
        for ax_index, (celltype, spiketrains) in enumerate(celltype_spiketrain_map.items()):
            ax = figure.add_subplot(len(celltype_spiketrain_map), 1, ax_index+1)
            spike_times = np.concatenate(spiketrains)
            n, bins, patches = ax.hist(spike_times,
                                       bins, 
                                       weights=np.ones(len(spike_times))/data.cellcounts._asdict()[celltype], 
                                       facecolor=colordict[celltype], 
                                       ec='none', 
                                       alpha=0.5, 
                                       label=celltype)
            max_height = max([p.get_bbox().get_points()[1][1] for p in patches])
            # Earlier simulations had a different dt used for
            # recording stimulus. So we need to extract that dt here
            # without depending on plotdt.
            num_stim_points = len(data.bg_stimulus)
            stim_dt = data.simtime / num_stim_points
            startindex = int(timerange[0]/stim_dt+0.5)
            endindex = int(timerange[1]/stim_dt+0.5) + 1            
            bg_stimulus = data.bg_stimulus[startindex:endindex]
            scale = max_height / max(bg_stimulus)
            ts = np.linspace(timerange[0], timerange[1], len(bg_stimulus))
            ax.plot(ts, bg_stimulus*scale, 'b-.', alpha=0.4, label='deepbasket=%d' % (data.cellcounts.DeepBasket))
            plt.legend()
        image_file = os.path.basename(data.fdata.filename)+'.hist.png'
        figure.set_size_inches(6,6)
        figure.savefig(image_file)
        print 'Saved plot in', image_file
        print data.get_notes()
    return figures

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


def display_more_tcr_stimulated_spike_hist(colordict):
    filenames = []
    with open('many_tcr_stimulated.txt', 'r') as filelist:
        for line in filelist:
            filename = line.strip()
            if filename:
                filenames.append(filename)
    handles = []
    for fname in filenames:
        try:
            fd = TraubData(fname)
            handles.append(fd)
        except (IOError, KeyError) as e:
            print e
    good_files = []    
    for fd in handles:
        if len(fd.bg_cells) > 5 \
          and fd.simtime >= 10.0 \
          and fd.cellcounts.TCR == 100 \
          and fd.cellcounts.SpinyStellate == 240 \
          and fd.cellcounts.SupPyrRS == 0 \
          and fd.cellcounts.SupLTS == 0 \
          and fd.cellcounts.SupBasket == 0 \
          and fd.cellcounts.SupPyrFRB == 0 \
          and fd.cellcounts.SupAxoaxonic == 0 \
          and fd.cellcounts.nRT == 0:
          good_files.append(fd)
    plot_population_spike_histogram(good_files, (0, 10.0), np.arange(0, 10.0, 5e-3), colordict)

def plot_exc_inh_balance(colordict):
    """Plot population spike histogram for the simulations between
    excitation inhibition balance.  These simulations for excitation
    inhibition balance were done from 2012-09-19 till 2012-11-23
    
    """
    files = []
    with open('exc_inh_files.txt', 'r') as filelist:
        for line in filelist:
            filename = line.strip()
            if filename:
                files.append(filename)    
    current_fts = get_fname_timestamps(files, '20120918', '20121123') 
    handles = []
    for fname in current_fts.keys():
        try:
            handles.append(TraubData(fname))
        except (IOError, KeyError) as e:
            print e
    plot_population_spike_histogram(handles, (0, 20.0), np.arange(0, 20.0, 5e-3), colordict)
    plt.show()

def find_intermediate_spinstells(data, fracoutofgroup=0.1, popfrac=0.5, timerange=(1.0, 1e9)):
    """Get the list of spiny stellate cells that fire in between
    population bursts/spikes. This can be used to see if the same
    cells fire in the same pattern.

    data: TraubData

    fracoutofgroup: fraction of times a cell must fire in the
    population interburst interval to qualify as an out of group cell.

    popfrac: fraction of the population that must burst in a bin to
    qualify that as a population burst.

    """
    bursting_hist, bins = data.get_bursting_cells_hist('SpinyStellate', timerange=(1.0, 1e9))
    bursting_hist /= 1.0 * data.cellcounts.SpinyStellate
    indices = np.nonzero(bursting_hist < popfrac)[0]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    strongly_out = []
    weakly_out = []
    count = 1
    lines = []
    cmap = plt.cm.copper_r
    for cell, spikes in data.spikes.items():
        if cell.startswith('SpinyStellate'):
            hist, b = np.histogram(spikes, bins)
            cindices = np.nonzero(hist)[0]
            print 1, cindices
            print 2, indices
            common = set(cindices).intersection(set(indices))
            print 3, common
            if len(common) > fracoutofgroup * len(indices):
                weakly_out.append(cell)
                ax.plot(data.spikes[cell], np.ones(len(data.spikes[cell]))*count, marker='x', color=cmap(len(common)*1.0/len(indices)))
                lines.append(len(common)*1.0/len(indices))
                count += 1
    ax.bar(bins[indices], height=np.ones(len(indices))*5, bottom=len(lines), width=(bins[1] - bins[0]), alpha=0.2)
    sm = plt.cm.ScalarMappable(cmap=cmap)
    sm.set_array(lines)
    plt.colorbar(sm)
    # ax.set_axis_bgcolor('black')
    # fig.patch.set_facecolor('black')
    plt.show()
    return (strongly_out, weakly_out)
    
        
if __name__ == '__main__':    
    data = TraubData('/data/subha/rsync_ghevar_cortical_data_clone/2012_11_05/data_20121105_144428_16400.h5')
    strong, weak = find_intermediate_spinstells(data)
    print strong
    print weak
    sys.exit(0)
    # plot_spinstell_sync_spike_with_num_deepbasket(0.2)
    # These simulations for excitation inhibition balance were done from 2012-09-19 till 2012-11-??
    # filenames = find_files('/data/subha/rsync_ghevar_cortical_data_clone', '-iname', 'data_*.h5') # Find all data files in the directory

    # current_fts = get_fname_timestamps(filenames, '20110101', '20120920') 
    # handles = []
    # for fname in current_fts.keys():
    #     try:
    #         handles.append(TraubData(fname))
    #     except (IOError, KeyError) as e:
    #         print e
    # print '=== printing filenames and notes ==='    
    # candidate_files = []
    # plot_population_spike_histogram(candidate_files, (0, 10.0), np.arange(0, 10.0, 5e-3), colordict)
    # plt.show()

    
    # categories = classify_files_by_cellcount(current_fts.keys())
    # # After categorising the good files, we work with only those files
    # # with 240 spiny stellate cells (others test simulations)
    # goodfiles = {cc: files for cc, files in categories.items() if cc.SpinyStellate == 240}
    # data = [TraubData(filename) for filenamelist in goodfiles.values() for filename in filenamelist]
    # print 'Loaded data'
    # for d in data:
    #     print d.fdata.filename
    #     print d.bg_cells
    #     cell_stimcount_list = []
    #     for cell in d.get_bg_stimulated_cells('SpinyStellate'):
    #         pre_cells = set([pre for pre in d.presynaptic(cell)])
    #         stim_pre_cells = pre_cells.intersection(set(d.bg_cells))
    #         cell_stimcount_list.append((cell, len(stim_pre_cells)))
    #     for cell, stim_count in sorted(cell_stimcount_list, key=itemgetter(1)):
    #         print cell, stim_count
            
    #     print d.probe_cells
    #     print 'Probe stimulated SS cells:'
    #     probed_cells = d.get_probe_stimulated_cells('SpinyStellate')
    #     print len(probed_cells)
        

    #============================================================
    # The following code plots population spike count histogram
    # start = 15.0
    # end = 20.0 + data[0].simdt
    # plot_population_spike_histogram(data, (start, end), np.arange(start, end, 5e-3), colordict)
    # print 'Created plots'
    # plt.show()
    # Population spike count histogram till here
    #============================================================
    # The following code is for plotting spike rasters for SpinyStellate and TCR cells
    # cellcounts=cellcount_tuple(SupPyrRS=0,
    #                            SupPyrFRB=0,
    #                            SupBasket=0,
    #                            SupAxoaxonic=0,
    #                            SupLTS=0,
    #                            SpinyStellate=240,
    #                            TuftedIB=0,
    #                            TuftedRS=0,
    #                            DeepBasket=0,
    #                            DeepAxoaxonic=0,
    #                            DeepLTS=0,
    #                            NontuftedRS=0,
    #                            TCR=100,
    #                            nRT=0)
    # data = {}
    # for cc, fnames in goodfiles.items():        
    #     data.update(load_spike_data(fnames))
    # print 'Loaded data from', len(data), 'files'
    # randomized_spike_rasters_allcelltype(goodfiles, data, cellcounts, colordict)
    # Till here
    #============================================================
        
                
# 
# analyze_excitation_inhibition_balance.py ends here
