# plot_stimulus_count_reponse.py --- 
# 
# Filename: plot_stimulus_count_reponse.py
# Description: 
# Author: 
# Maintainer: 
# Created: Mon Mar  4 10:41:54 2013 (+0530)
# Version: 
# Last-Updated: Fri Mar 29 16:21:17 2013 (+0530)
#           By: subha
#     Update #: 107
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# Plot the spike rasters for varying number of stimulus in order to
# see the effect of stimulating more TCR cells.
# 
# 

# Change log:
# 
# 
# 
# 

# Code:

import os
from datetime import datetime
from collections import defaultdict
import numpy as np

from traubdata import TraubData

# Dictionary containing the mapping from stimulated cell count to data files
stimcnt_fnames = {
    5: ['data_20121114_091030_2716.h5',
        'data_20121116_091100_3774.h5', 
        'data_20121118_132702_5610.h5', 
        'data_20121120_090612_6590.h5', 
        'data_20121122_145449_8016.h5'],
    10: ['data_20121124_162657_9363.h5',
         'data_20121126_092942_10181.h5',
         'data_20121128_092639_11369.h5',
         'data_20121130_083256_12326.h5',
         'data_20121205_165444_16910.h5',],
    15: ['data_20121208_105807_15611.h5',
         'data_20121211_103522_12008.h5',
         'data_20121214_095338_17603.h5',
         'data_20121218_090355_29114.h5',
         'data_20121221_151958_9665.h5'],
    20:['data_20130119_114614_12793.h5',
        'data_20130121_150010_15584.h5',
        'data_20130123_091433_23206.h5',
        'data_20130125_120631_30768.h5',
        'data_20130128_230854_32444.h5',]
    }

datadir = '/data/subha/rsync_ghevar_cortical_data_clone'

def load_files():
    """Check that the files in map from stimcount to filename are
    correct"""
    cellcount = None
    fdict = defaultdict(list)
    for stimcount, flist in stimcnt_fnames.items():        
        for filename in flist:
            ts = filename.partition('_')[-1].rpartition('_')[0]
            print ts
            ts = datetime.strptime(ts, '%Y%m%d_%H%M%S')
            fpath = os.path.join(datadir, ts.strftime('%Y_%m_%d'), filename)
            print fpath
            data = TraubData(fpath)
            # Confirm that the stimulus count matches in our dict as
            # well as in the actual data file.
            assert(int(dict(np.asarray(data.fdata['/runconfig/stimulus']))['bg_count']) == stimcount)
            new_cellcount = data.cellcounts
            if cellcount is not None:
                assert(new_cellcount == cellcount)
            cellcount = new_cellcount
            fdict[stimcount].append(data)
    return fdict
    
from matplotlib import pyplot as plt 

def plot_stimcount_response():
    stimcount_datalist = load_files()
    figidx = 1
    dt = 100e-3
    for stimcount, datalist in stimcount_datalist.items():
        fig = plt.figure(figidx)
        fig.suptitle('%d TCR stimulated' % (stimcount))
        figidx += 1
        axs = None
        for idx, data in enumerate(datalist):
            axs = fig.add_subplot(len(datalist), 1, idx+1, sharex=axs, sharey=axs)
            ss = [data.spikes['SpinyStellate_%d' % (ii)] for ii in range(data.cellcounts._asdict()['SpinyStellate'])]
            stimtimes = data.get_bgstim_times()
            sspst = [np.concatenate([st[(st > t) & (st <= t + dt)] for t in stimtimes]) for st in ss ]
            # tcr = [data.spikes['TCR_%d' % (ii)] for ii in range(data.cellcounts._asdict()['TCR'])]
            ll = [axs.plot(st, np.ones(len(st))*(ii+1), 'r,', mew=0) for ii, st in enumerate(sspst)]
            # ll = [axs.plot(st, np.ones(len(st))*(ii+1+len(tcr)), 'b,', mew=0) for ii, st in enumerate(ss)]
            axs.plot(np.linspace(0, data.simtime, len(data.bg_stimulus)), axs.yaxis.get_data_interval()[1] * data.bg_stimulus/max(data.bg_stimulus) , 'g-', alpha=0.5)
            # axs.set_xlim((15, 20))
    plt.show()
    return stimcount_datalist

if __name__ == '__main__':
    plot_stimcount_response()

# 
# plot_stimulus_count_reponse.py ends here
