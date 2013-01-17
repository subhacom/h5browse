# analyze_stimulus_response.py --- 
# 
# Filename: analyze_stimulus_response.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Jan  2 10:07:34 2013 (+0530)
# Version: 
# Last-Updated: Thu Jan 17 19:22:02 2013 (+0530)
#           By: subha
#     Update #: 667
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# This script is for looking at response to stimulus in the spiny
# stellate cells.
# 
# 

# Change log:
# 
# 
# 
# 

# Code:

import random
import os
from collections import defaultdict
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from traubdata import TraubData

def get_cells_responding_to_bg(data):
    """Get the TCR cells responding to background stimulus
    """
    bg_times = data.get_bgstim_times()    
    # Choose the TCR cells from the background stimulated set that
    # spiked at least once after 1 s (during which time spurious
    # spiking due to instabilities may occur). Not all stimulated TCR
    # cells spiked.
    stimcells = [cell for cell in data.spikes.keys() \
                     if cell.startswith('TCR') and \
                     np.any(data.spikes[cell] > 1.0) and \
                     cell in data.bg_cells]
    goodstimcells = []
    # plt.figure()
    # plt.plot(bg_times, np.zeros(len(bg_times)), 'g^')
    for idx, cell in enumerate(stimcells):
        # Ignore cells which spiked too-much without stimulus
        sp = data.spikes[cell].copy()        
        # Check how many times the cell spiked in an interstimulus
        # interval with 50 ms margin
        outofturn = [np.any(( sp > bg_times[ii]+50e-3) & 
                            (sp < bg_times[ii+1] - 50e-3)) \
                         for ii in range(len(bg_times)-1)]
        # If number of spikes without stimulus is less than
        # half(arbitrarily chosen) the number of stimuli, this is a
        # good cell
        if np.nonzero(outofturn)[0].shape[0] < len(bg_times)/2.0:
            goodstimcells.append(cell)
            # plotmarker = 'rx'
        # else:
        #     plotmarker = 'b+'
    #     plt.plot(sp, np.ones(len(sp))*(idx+1), plotmarker)
    # plt.show()
    # print set(data.bg_cells) - set(goodstimcells)
    return goodstimcells
    #     if 0 in outofturn.shape:
    #         continue
    #     plt.plot(outofturn, np.ones(len(outofturn))*(idx+1), 'rx')
    #     print cell, outofturn
    # plt.show()

def test_get_cells_responding_to_bg():
    for fname in fname_stim_dict.keys():
        get_cells_responding_to_bg(TraubData(fname))

def stimresponse(datalist, cells, figlabel='1'):
    colormap = plt.cm.jet
    plt.close()
    ax = None
    axlist = []
    # Go through each data file, pick up the stimulated cells
    fig1 = plt.figure(figlabel)
    # fig2 = plt.figure(2)
    for di, data in enumerate(datalist):
        if isinstance(cells, str):
            cells = set([cell for cell in data.spikes.keys() if cell.startswith(cells)])
        stimulated_cells = get_cells_responding_to_bg(data)
        post_cells = [data.postsynaptic(pre) \
                          for pre in stimulated_cells]
        inputcounts = defaultdict(int)
        for celllist in post_cells:
            for cell in set(celllist).intersection(cells):
                inputcounts[cell] += 1
        inputcount_cell_map = defaultdict(list)
        for cell, count in inputcounts.items():
            inputcount_cell_map[count].append(cell)
        ax = fig1.add_subplot(len(datalist), 1, di+1)
        # ax.set_title(data.fdata.filename)
        # ax2 =fig2.add_subplot(len(datalist), 1, di+1)
        # ax2.set_title(data.fdata.filename)
        norm = mpl.colors.Normalize(vmin=1, vmax=max(inputcount_cell_map.keys()))
        mappable = mpl.cm.ScalarMappable(norm=norm, cmap=colormap)
        carray = np.arange(1, 10)
        mappable.set_array(carray)
        pop_ibi = data.get_pop_ibi(cells, maxisi=30e-3)['pop_ibi']
        ci = 1 # index of the cell in the raster plot (used as Y)
        cellcount = 0 # (total number of cells)
        for count in sorted(inputcount_cell_map.keys()):
            print count, len(inputcount_cell_map[count])
            for cell in inputcount_cell_map[count]:
                pre = set(data.presynaptic(cell)).intersection(stimulated_cells)
                assert(count == len(pre))
                spikes = data.spikes[cell]
                # ax2.plot(spikes, np.ones(len(spikes)) * ci, 'bx')
                nonpopspikes = []
                for ibi in zip(*pop_ibi):
                    # print 'IBI:', ibi
                    nonpopspikes.append(spikes[(spikes >= ibi[0]) & (spikes < ibi[1])])
                # print 'Number of bunches in pop-ibi', len(nonpopspikes)
                # print nonpopspikes
                spikes = np.concatenate(nonpopspikes)
                peristim_spikes = np.concatenate([spikes[(spikes > t) & (spikes < t + 50e-3)] for t in data.get_bgstim_times()])
                if len(np.nonzero(peristim_spikes)[0]) >= len(data.get_bgstim_times()) * 0.5:
                    ax.plot(spikes, np.ones(len(spikes)) * ci, ',', mew=0.0, color=mappable.to_rgba(count))                
                    ci += 1
                cellcount += 1
        print 'number of cells', ci
        ax.plot(data.get_bgstim_times(), np.zeros(len(data.get_bgstim_times())), '^')
        # ax.bar(pop_ibi[0], height=np.ones(len(pop_ibi[0]))*ci, width=np.array(pop_ibi[1])-np.array(pop_ibi[0]), alpha=0.5)
        ylim = ax.get_ylim()
        dy = 1
        if ylim[1] - ylim[0] > 10:
            dy = (ylim[1] - ylim[0])/5
        yticks = range(int(ylim[0]), int(ylim[1]), int(dy))
        ax.set_yticks(yticks)
        # ax.patch.set_facecolor('black')
        ylabels = ax.set_yticklabels([str(label) for label in yticks])
        # print 'ylim', ax.get_ylim()
        cbar = plt.colorbar(mappable)
        ticks = range(carray[0], carray[-1])
        cbar.set_ticks(ticks)
        cbar.set_ticklabels(['%d' % (t) for t in ticks])
    return fig1
    # plt.show()
    # plt.close()

def test_stim_response():
    # datalist = [TraubData(fname) for fname in random.sample(fname_stim_dict.keys(), 2)]
    datalist = [TraubData(fname) for fname in fname_stim_dict.keys()]
    stimresponse(datalist, 'SpinyStellate')


def check_stimulus_response(datalist, cells):
    colormap = plt.cm.jet
    fig = plt.figure()
    ax = None
    axlist = []
    rows = len(datalist)
    for dataindex, data in enumerate(datalist):
        # print data.fdata.filename, data.cellcounts.DeepBasket
        # Select the cells of celltype
        if isinstance(cells, str):
            cells = [cell for cell in data.spikes.keys() if cell.startswith(cells)]
        stimtimes = data.get_bgstim_times()
        popibi = data.get_pop_ibi(cells)['pop_ibi']
        cells = set(cells)
        # select TCR cells  which spiked beyond first second, which can have spurious spikes due to simulation instabilities
        stimcells = [cell for cell in data.spikes.keys() if cell.startswith('TCR') and np.any(data.spikes[cell] > 1.0)]
        stimcells = [cell for cell in stimcells if len(data.spikes[cell]) < 2*len(stimtimes)]
        stims = np.concatenate([data.spikes[cell] for cell in stimcells if len(data.spikes[cell]) > 0])
        filtered = np.concatenate([stims[(stims > start+50e-3) & (stims < end-50e-3)].copy() for start, end in zip(popibi[0], popibi[1])])    
        # print filtered
        stims = filtered
        postcells = [post for pre in stimcells for post in data.postsynaptic(pre) if post in cells]
        inputcounts = defaultdict(list)
        for cell in postcells:
            indices = np.char.startswith(data.synapse['dest'], cell+'/')
            precells = [row[0] for row in np.char.split(data.synapse['source'][indices], '/') if row[0] in stimcells]
            inputcounts[len(precells)].append(cell)
        # print inputcounts        
        ax = fig.add_subplot(rows, 1, dataindex+1, sharex=ax)
        # ax.set_title('%s: %d' % (data.fdata.filename, data.cellcounts.DeepBasket))
        axlist.append(ax)
        ax.plot(filtered, np.zeros(len(filtered)), '^', label='TCR spikes')
        cellindex = 1
        norm = mpl.colors.Normalize(vmin=1, vmax=max(inputcounts.keys()))
        mappable = mpl.cm.ScalarMappable(norm=norm, cmap=colormap)
        mappable.set_array(np.arange(1, 10))
        for count in sorted(inputcounts.keys()):
            for cell in inputcounts[count]:
                spikes = data.spikes[cell]
                spikes = spikes[spikes > 1.0].copy()
                peristim_spikes = np.concatenate([spikes[np.nonzero((spikes > t) & (spikes < t + 50e-3))[0]] for t in stims])
                if len(np.nonzero(peristim_spikes)[0]) < 10:
                    continue
                # print len(np.nonzero(peristim_spikes)[0])
                ax.plot(peristim_spikes, np.ones(len(peristim_spikes)) * cellindex, 'x', color=mappable.to_rgba(count))
                cellindex += 1
        st = stimtimes[stimtimes > 1.0].copy()    
        plt.colorbar(mappable)
    for ax in axlist[1:]:
        ax.xaxis.set_visible(False)
        # ax.yaxis.set_visible(False)
    # plt.savefig('stimulus_response.png')
    plt.show()

datadir = '/data/subha/rsync_ghevar_cortical_data_clone/'
# These paths are for ghevar
filenames = [
'2012_09_19/data_20120919_172536_12276.h5',
'2012_10_03/data_20121003_091501_19886.h5',
'2012_11_08/data_20121108_210758_30357.h5',
'2012_11_22/data_20121122_145449_8016.h5']

"""cellcount(SupPyrRS=0, SupPyrFRB=0, SupBasket=0, SupAxoaxonic=0, SupLTS=0, SpinyStellate=240, TuftedIB=0, TuftedRS=0, DeepBasket=60, DeepAxoaxonic=0, DeepLTS=30, NontuftedRS=0, TCR=100, nRT=0)
	/data/subha/rsync_ghevar_cortical_data_clone/2012_12_08/data_20121208_105807_15611.h5 15
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_30/data_20121130_083256_12326.h5 10
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_22/data_20121122_145449_8016.h5 5
	/data/subha/rsync_ghevar_cortical_data_clone/2012_12_05/data_20121205_165444_16910.h5 10
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_20/data_20121120_090612_6590.h5 5
	/data/subha/rsync_ghevar_cortical_data_clone/2012_12_21/data_20121221_151958_9665.h5 15
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_26/data_20121126_092942_10181.h5 10
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_16/data_20121116_091100_3774.h5 5
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_24/data_20121124_162657_9363.h5 10
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_28/data_20121128_092639_11369.h5 10
	/data/subha/rsync_ghevar_cortical_data_clone/2012_12_11/data_20121211_103522_12008.h5 15
	/data/subha/rsync_ghevar_cortical_data_clone/2012_12_14/data_20121214_095338_17603.h5 15
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_14/data_20121114_091030_2716.h5 5
	/data/subha/rsync_ghevar_cortical_data_clone/2012_12_18/data_20121218_090355_29114.h5 15
	/data/subha/rsync_ghevar_cortical_data_clone/2012_11_18/data_20121118_132702_5610.h5 5"""

fname_stim_dict = {
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_14/data_20121114_091030_2716.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_16/data_20121116_091100_3774.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_18/data_20121118_132702_5610.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_20/data_20121120_090612_6590.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_22/data_20121122_145449_8016.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_24/data_20121124_162657_9363.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_26/data_20121126_092942_10181.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_28/data_20121128_092639_11369.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_30/data_20121130_083256_12326.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_05/data_20121205_165444_16910.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_08/data_20121208_105807_15611.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_11/data_20121211_103522_12008.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_14/data_20121214_095338_17603.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_18/data_20121218_090355_29114.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_21/data_20121221_151958_9665.h5': 15,
    }

def plot_stimcount_response():
    """Plot stimulus response for each stimulus count"""
    stim_fname = defaultdict(list) # Stimulus count -> data-list map
    for k, v in fname_stim_dict.items():
        stim_fname[v].append(k)
    # Now we do the plotting for each stimulus count in increasing order
    for key in sorted(stim_fname.keys()):
        fig = stimresponse([TraubData(fname) for fname in stim_fname[key]], 'SpinyStellate', 'Stimulated TCR: %d' % (key))
        fig.suptitle('Stimulated TCR: %d' % (key))
        plt.show()

def plot_stim_response():
    """Plot stimulus response for each stimulus count"""
    stim_fname = defaultdict(list) # Stimulus count -> data-list map
    for k, v in fname_stim_dict.items():
        stim_fname[v].append(k)
    # Now we do the plotting for each stimulus count in increasing order
    for key in sorted(stim_fname.keys()):
        check_stimulus_response([TraubData(fname) for fname in stim_fname[key]], 'SpinyStellate')
        

def plot_spikeraster_by_stim_count(timerange=(10.0, 12.0)):
    cm = plt.cm.jet    
    stim_fname = defaultdict(list)
    for k, v in fname_stim_dict.items():
        stim_fname[v].append(k)    
    figures = []
    for k, v in stim_fname.items():
        f = plt.figure()
        legend_rects = []
        legend_texts = []
        cols = len(v)
        ax = None
        for ii, fname in enumerate(v):
            ax = f.add_subplot(1, cols, ii+1, sharex=ax, sharey=ax)
            ax.set_title('\n'.join(textwrap.wrap(fname, 32)))
            ax.patch.set_facecolor('black')
            data = TraubData(fname)
            ctypeidx = 0
            norm = mpl.colors.Normalize(vmin=0, vmax=len(data.cellcounts))
            mappable = mpl.cm.ScalarMappable(norm=norm, cmap=cm)
            mappable.set_array(np.arange(0, len(data.cellcounts)))
            cellindex = 1
            cells = set()
            for celltype, count in data.cellcounts._asdict().items():
                print celltype,ctypeidx, count
                for cidx in range(count):
                    cell = '%s_%d' % (celltype, cidx)
                    spikes = data.spikes[cell].copy()
                    spikes = spikes[(spikes > timerange[0]) & (spikes < timerange[1])].copy()
                    color = mappable.to_rgba(ctypeidx*1.0)
                    # print ctypeidx, color
                    ax.plot(spikes, np.ones(len(spikes)) * cellindex, ',', color=color, mew=0.0)
                    cellindex += 1
                    cells.add(cell)
                ctypeidx += 1
            assert(len(cells.intersection(set(data.spikes.keys()))) == len(cells))
            if ii == 0:
                for ctypeidx, celltype in enumerate(data.cellcounts._asdict().keys()):
                    if data.cellcounts._asdict()[celltype] > 0:
                        legend_rects.append(plt.Rectangle((0, 0), 1, 1, fc=mappable.to_rgba(ctypeidx)))
                        legend_texts.append(celltype)
        # f.canvas.mpl_connect('draw_event', on_draw)
        # f.patch.set_facecolor('black')
        f.legend(legend_rects, legend_texts, 'upper right')
        f.suptitle('%d stimuli' % (k))
        plt.show()
        plt.close()

## Used for manually creating fname_stim_dict and discarded
# import os
# import subprocess as sp
# import get_files_by_ts as gft
# def get_file_notes(directory, *args):
#     """Scratch utility to get the notes from files and the cell counts"""
#     flist = gft.find_files(directory, *args)
#     fdict = gft.get_fname_timestamps(flist, start='20120901')
#     cats = gft.classify_files_by_cellcount(fdict.keys())
#     for k, v in cats.items():
#         print k
#         for x in v:
#             d = TraubData(x)            
#             print '\t', x, dict(d.fdata['/runconfig/stimulus'])['bg_count']
    
        
if __name__ == '__main__':
    plot_stimcount_response()
    # test_stim_response()
    # test_get_cells_responding_to_bg()
    # plot_stim_response()
    # plot_spikeraster_by_stim_count()
    # get_file_notes(datadir, '-mtime', '-140', '-iname', 'data*.h5')
    # check_stimulus_response([TraubData(os.path.join(datadir, filename)) for filename in filenames], 'SpinyStellate')

# 
# analyze_stimulus_response.py ends here
