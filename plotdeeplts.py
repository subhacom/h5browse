# plotdeeplts.py --- 
# 
# Filename: plotdeeplts.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Jan 30 16:40:09 2013 (+0530)
# Version: 
# Last-Updated: Thu Jan 31 15:08:53 2013 (+0530)
#           By: subha
#     Update #: 87
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

# Code:
import random
import os
from collections import defaultdict
import numpy as np
import matplotlib as mpl
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import sys
sys.path.append(os.path.expanduser('~/src/dataviz'))
from traubdata import TraubData

datadir = '/data/subha/cortical/py/data'
import socket
if socket.gethostname() == 'chamcham':
    datadir = '/data/subha/rsync_ghevar_cortical_data_clone'

fname_stim_dict = {
    '2012_11_14/data_20121114_091030_2716.h5': 5,
    '2012_11_16/data_20121116_091100_3774.h5': 5,
    '2012_11_18/data_20121118_132702_5610.h5': 5,
    '2012_11_20/data_20121120_090612_6590.h5': 5,
    '2012_11_22/data_20121122_145449_8016.h5': 5,
    '2012_11_24/data_20121124_162657_9363.h5': 10,
    '2012_11_26/data_20121126_092942_10181.h5': 10,
    '2012_11_28/data_20121128_092639_11369.h5': 10,
    '2012_11_30/data_20121130_083256_12326.h5': 10,
    '2012_12_05/data_20121205_165444_16910.h5': 10,
    '2012_12_08/data_20121208_105807_15611.h5': 15,
    '2012_12_11/data_20121211_103522_12008.h5': 15,
    '2012_12_14/data_20121214_095338_17603.h5': 15,
    '2012_12_18/data_20121218_090355_29114.h5': 15,
    '2012_12_21/data_20121221_151958_9665.h5': 15,
    '2013_01_19/data_20130119_114614_12793.h5': 20,
    '2013_01_21/data_20130121_150010_15584.h5': 20,
    '2013_01_23/data_20130123_091433_23206.h5': 20,
    '2013_01_25/data_20130125_120631_30768.h5': 20,
    '2013_01_28/data_20130128_230854_32444.h5': 20
    }

def plot_spikes_with_stimcount(celltype):
    stim_data_dict = defaultdict(list)
    for key, value in fname_stim_dict.items():
        stim_data_dict[value].append(os.path.join(datadir, key))
    # Go through each stimulus count
    for fidx, stimcount in enumerate(sorted(stim_data_dict.keys())):
        fig = plt.figure(fidx+1)
        fig.suptitle('%d' % (stimcount))
        spikeax = None #  X and Y of the firstaxis will be shared by all of them
        psthax = None
        filelist = stim_data_dict[stimcount]
        subplotcount = len(filelist)
        for sidx, fname in enumerate(filelist):
            spikeax = fig.add_subplot(subplotcount, 2, 2*sidx+1, sharex=spikeax, sharey=spikeax)
            spikeax.set_title(fname)
            psthax = fig.add_subplot(subplotcount, 2, 2*(sidx+1), sharex=psthax, sharey=psthax)
            data = TraubData(fname)
            bgtimes = data.get_bgstim_times()
            cid = 0 # Track the cell no.
            combined_spikes = []
            for cellname, spikes in data.spikes.items():
                if cellname.startswith(celltype):
                    cid +=1
                    spikeax.plot(spikes, np.ones(len(spikes))*cid, 'k,', mew=0)
                    combined_spikes = np.r_[combined_spikes, spikes]
            bins = np.arange(0, data.simtime+50e-3, 50e-3)
            bg = data.bg_stimulus
            gaussian = np.exp(-(np.arange(0, 1, int(100e-3/data.plotdt))**2))
            psthax.plot(np.convolve(gaussian, bg))
            psthax.plot(np.convolve(gaussian, combined_spikes))
            psthax.plot(bg)
            break
            # psthax.hist(combined_spikes, bins, rwidth=50e-3, histtype='bar', lw=0)
            spikeax.plot(bgtimes, np.zeros(len(bgtimes)), 'r^')
            psthax.plot(bgtimes, np.zeros(len(bgtimes)), 'r^')
    plt.show()


if __name__ == '__main__':
    plot_spikes_with_stimcount('DeepBasket')


# 
# plotdeeplts.py ends here
