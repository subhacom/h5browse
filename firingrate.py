# firingrate.py --- 
# 
# Filename: firingrate.py
# Description: 
# Author: 
# Maintainer: 
# Created: Thu Dec 29 11:40:39 2011 (+0530)
# Version: 
# Last-Updated: Thu Dec 29 11:53:04 2011 (+0530)
#           By: subha
#     Update #: 23
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# compute firing rates
# 
# 

# Change log:
# 
# 
# 
# 

# Code:

import numpy as np
import pylab as pl
import h5py as h5

def compute_firing_rate(spike_times, t_total, binsize=1.0, t_start=0.0, t_end=-1.0):
    if t_end <= 0.0:
        t_end = t_total
    num_bins = 2.0 * (t_end - t_start) / binsize - 1
    firing_rate = np.zeros(num_bins)
    t = 0.0
    for ii in range(num_bins):
        for spike_time in spike_times:
            if spike_time < t_start:
                continue
            if spike_time > t_end or spike_time > t+binsize/2.0:
                break
            if (t - binsize/2.0) < spike_time and (t + binsize/2.0) > spike_time:
                print 'Adding', spike_time, 'to bin centred at', t
                firing_rate[ii] += 1.0
        t += binsize/2.0
    return firing_rate




# 
# firingrate.py ends here
