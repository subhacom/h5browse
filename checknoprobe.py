# checknoprobe.py --- 
# 
# Filename: checknoprobe.py
# Description: 
# Author: 
# Maintainer: 
# Created: Mon Jun 25 16:13:04 2012 (+0530)
# Version: 
# Last-Updated: Mon Jun 25 21:07:32 2012 (+0530)
#           By: subha
#     Update #: 162
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# This script is for checking the average no of spikes after each
# stimulus. Even when no probe stimulus is applied, the even numbered
# bg stimulus shows different behaviour in bgprobe_run.py. This script
# is for addressing that.
# 
# 

# Change log:
# 
# 
# 
# 

# Code:

import numpy as np
import h5py as h5
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime
from mpl_toolkits import mplot3d as m3

files = [
    # 'data_20120128_120809_21820.h5',
    'data_20120128_120931_21882.h5',
    # 'data_20120510_171659_3930.h5',
    # 'data_20120510_173715_4036.h5',
    # 'data_20120511_162701_5850.h5',
    # 'data_20120513_210447_9261.h5',
    # 'data_20120509_184603_2179.h5',
    # 'data_20120512_142746_7319.h5',
    # 'data_20120507_194518_31778.h5',
    # 'data_20120119_135900_9148.h5',
    # 'data_20120119_132336_9035.h5',
    # 'data_20120106_152224_16193.h5',
    # 'data_20120424_145719_7507.h5'
]

if __name__ == '__main__':
    celltype = 'SpinyStellate'
    dname = '/data/subha/rsync_ghevar_cortical_data_clone/'
    for fname in files:        
        fdate = fname.split('_')[1]
        ymd = datetime.strptime(fdate, '%Y%m%d')        
        fpath = dname+ymd.strftime('%Y_%m_%d')+'/'+fname
        print 'Opning', fpath
        df = h5.File(fpath, 'r')        
        print 'Processing:', fname
        bg = df['stimulus/stim_bg'][:]
        dt = float(df.attrs['simtime']) / len(bg)
        print 'dt =', dt
        bgtimes = np.nonzero(np.diff(bg) > 0)[0] * dt
        print 'Backgrounds at:'
        print bgtimes
        datadict = defaultdict(list)
        odddict = {}
        evendict = {}
        oddtfs = defaultdict(list)
        eventfs = defaultdict(list)
        for cell in df['spikes']:
            if not cell.startswith(celltype):
                continue
            spiketimes = df['spikes'][cell][:]
            print 'Spike times',
            print spiketimes
            odds = []
            evens = []
            for ii in range(1, len(bgtimes)):
                spikes = spiketimes[(spiketimes >= bgtimes[ii-1]) & (spiketimes < bgtimes[ii])] - bgtimes[ii-1]
                print ii, spikes
                datadict[cell].append(spikes)
                if ii % 2 == 1:
                    tfs = oddtfs
                    counts = odds
                else:
                    tfs = eventfs
                    counts = evens
                l = len(spikes)
                if l > 0:
                    tfs[cell].append(spikes[0])
                else:
                    tfs[cell].append(-1.0)
                counts.append(l)
            odddict[cell] = odds
            evendict[cell] = evens
        oddmean = [np.mean(v) for v in odddict.values()]
        evenmean = [np.mean(v) for v in evendict.values()]
        oddtfsmean = [np.mean(v) for v in oddtfs.values()]
        eventfsmean  = [np.mean(v) for v in eventfs.values()]
        plt.subplot(4,1,1)
        plt.title('avg odd')
        plt.hist(oddmean)
        plt.subplot(4,1,2)
        plt.title('avg even')
        plt.hist(evenmean)
        plt.subplot(4, 1, 3)
        plt.title('tfs vs spike count')
        plt.scatter(oddtfsmean, oddmean, c='c', marker='x')
        plt.scatter(eventfsmean, evenmean, c='m', marker='+')
        plt.show()

# 
# checknoprobe.py ends here
