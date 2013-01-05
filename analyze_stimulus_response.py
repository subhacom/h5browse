# analyze_stimulus_response.py --- 
# 
# Filename: analyze_stimulus_response.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Jan  2 10:07:34 2013 (+0530)
# Version: 
# Last-Updated: Sat Jan  5 15:15:48 2013 (+0530)
#           By: subha
#     Update #: 182
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
        
if __name__ == '__main__':
    check_stimulus_response([TraubData(os.path.join(datadir, filename)) for filename in filenames], 'SpinyStellate')

# 
# analyze_stimulus_response.py ends here
