# analyze_stimulus_response.py --- 
# 
# Filename: analyze_stimulus_response.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Jan  2 10:07:34 2013 (+0530)
# Version: 
# Last-Updated: Fri Jan 11 16:32:59 2013 (+0530)
#           By: subha
#     Update #: 329
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

import os
from collections import defaultdict
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from traubdata import TraubData

def check_stimulus_response(datalist, cells):
    colormap = plt.cm.jet
    fig = plt.figure()
    ax = None
    axlist = []
    for dataindex, data in enumerate(datalist):
        print data.fdata.filename, data.cellcounts.DeepBasket
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
        print filtered
        stims = filtered
        postcells = [post for pre in stimcells for post in data.postsynaptic(pre) if post in cells]
        inputcounts = defaultdict(list)
        for cell in postcells:
            indices = np.char.startswith(data.synapse['dest'], cell+'/')
            precells = [row[0] for row in np.char.split(data.synapse['source'][indices], '/') if row[0] in stimcells]
            inputcounts[len(precells)].append(cell)
        print inputcounts        
        ax = fig.add_subplot(4, 1, dataindex+1, sharex=ax)
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
                print len(np.nonzero(peristim_spikes)[0])
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
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_08/data_20121208_105807_15611.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_30/data_20121130_083256_12326.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_22/data_20121122_145449_8016.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_05/data_20121205_165444_16910.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_20/data_20121120_090612_6590.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_21/data_20121221_151958_9665.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_26/data_20121126_092942_10181.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_16/data_20121116_091100_3774.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_24/data_20121124_162657_9363.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_28/data_20121128_092639_11369.h5': 10,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_11/data_20121211_103522_12008.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_14/data_20121214_095338_17603.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_14/data_20121114_091030_2716.h5': 5,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_12_18/data_20121218_090355_29114.h5': 15,
    '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_18/data_20121118_132702_5610.h5': 5,
    }

def on_draw(event):
    """Auto-wraps all text objects in a figure at draw-time

    Lifted from
    http://stackoverflow.com/questions/8802918/my-matplotlib-title-gets-cropped which lifted it from

    http://stackoverflow.com/questions/4018860/text-box-in-matplotlib/4056853#4056853
    """
    import matplotlib as mpl
    fig = event.canvas.figure
    # This does not work as we do not have axes associated with the text at top level
    # for artist in fig.get_children():
    #     # If it's a text artist, wrap it...
    #     if isinstance(artist, mpl.text.Text):
    #         autowrap_text(artist, event.renderer)
    # Cycle through all artists in all the axes in the figure
    for ax in fig.axes:
        for artist in ax.get_children():
            # If it's a text artist, wrap it...
            if isinstance(artist, mpl.text.Text):
                autowrap_text(artist, event.renderer)

    # Temporarily disconnect any callbacks to the draw event...
    # (To avoid recursion)
    func_handles = fig.canvas.callbacks.callbacks[event.name]
    fig.canvas.callbacks.callbacks[event.name] = {}
    # Re-draw the figure..
    fig.canvas.draw()
    # Reset the draw event callbacks
    fig.canvas.callbacks.callbacks[event.name] = func_handles

import textwrap

def autowrap_text(textobj, renderer):
    """Wraps the given matplotlib text object so that it exceed the boundaries
    of the axis it is plotted in.

    Lifted from
    http://stackoverflow.com/questions/8802918/my-matplotlib-title-gets-cropped which lifted it from

    http://stackoverflow.com/questions/4018860/text-box-in-matplotlib/4056853#4056853
    """
    # Get the starting position of the text in pixels...
    x0, y0 = textobj.get_transform().transform(textobj.get_position())
    # Get the extents of the current axis in pixels...
    clip = textobj.get_axes().get_window_extent()
    # Set the text to rotate about the left edge (doesn't make sense otherwise)
    textobj.set_rotation_mode('anchor')

    # Get the amount of space in the direction of rotation to the left and 
    # right of x0, y0 (left and right are relative to the rotation, as well)
    rotation = textobj.get_rotation()
    right_space = min_dist_inside((x0, y0), rotation, clip)
    left_space = min_dist_inside((x0, y0), rotation - 180, clip)

    # Use either the left or right distance depending on the horiz alignment.
    alignment = textobj.get_horizontalalignment()
    if alignment is 'left':
        new_width = right_space 
    elif alignment is 'right':
        new_width = left_space
    else:
        new_width = 2 * min(left_space, right_space)

    # Estimate the width of the new size in characters...
    aspect_ratio = 0.5 # This varies with the font!! 
    fontsize = textobj.get_size()
    pixels_per_char = aspect_ratio * renderer.points_to_pixels(fontsize)

    # If wrap_width is < 1, just make it 1 character
    wrap_width = max(1, new_width // pixels_per_char)
    try:
        wrapped_text = textwrap.fill(textobj.get_text(), wrap_width)
    except TypeError:
        # This appears to be a single word
        wrapped_text = textobj.get_text()
    textobj.set_text(wrapped_text)

def min_dist_inside(point, rotation, box):
    """Gets the space in a given direction from "point" to the boundaries of
    "box" (where box is an object with x0, y0, x1, & y1 attributes, point is a
    tuple of x,y, and rotation is the angle in degrees)

    Lifted from
    http://stackoverflow.com/questions/8802918/my-matplotlib-title-gets-cropped which lifted it from

    http://stackoverflow.com/questions/4018860/text-box-in-matplotlib/4056853#4056853
    """
    from math import sin, cos, radians
    x0, y0 = point
    rotation = radians(rotation)
    distances = []
    threshold = 0.0001 
    if cos(rotation) > threshold: 
        # Intersects the right axis
        distances.append((box.x1 - x0) / cos(rotation))
    if cos(rotation) < -threshold: 
        # Intersects the left axis
        distances.append((box.x0 - x0) / cos(rotation))
    if sin(rotation) > threshold: 
        # Intersects the top axis
        distances.append((box.y1 - y0) / sin(rotation))
    if sin(rotation) < -threshold: 
        # Intersects the bottom axis
        distances.append((box.y0 - y0) / sin(rotation))
    return min(distances)

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
    plot_spikeraster_by_stim_count()
    # get_file_notes(datadir, '-mtime', '-140', '-iname', 'data*.h5')
    # check_stimulus_response([TraubData(os.path.join(datadir, filename)) for filename in filenames], 'SpinyStellate')

# 
# analyze_stimulus_response.py ends here
