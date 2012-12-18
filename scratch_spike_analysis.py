# scratch_spike_analysis.py --- 
# 
# Filename: scratch_spike_analysis.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Dec 12 11:43:23 2012 (+0530)
# Version: 
# Last-Updated: Tue Dec 18 14:54:08 2012 (+0530)
#           By: subha
#     Update #: 161
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

import numpy as np
from matplotlib import pyplot as plt
from traubdata import TraubData
import peakdetect as pdet
import analyzer
from savitzkygolay import savgol

        

if __name__ == '__main__':
    data = TraubData('/data/subha/rsync_ghevar_cortical_data_clone/2012_11_07/data_20121107_100729_29479.h5')
    cats = data.get_pop_ibi('SpinyStellate')
    
            
    
    # combined_spikes = []
    # for cell, spiketimes in data.spikes.items():
    #     if cell.startswith('Spiny'):
    #         # np.savetxt('testspiketrain.txt', spiketimes)
    #         start, length, RS = ranksurprise.burst(spiketimes, 20e-3, 5.0)
    #         end = start+length-1
    #         plt.plot(spiketimes, np.ones(len(spiketimes)), 'rx')
    #         plt.plot(spiketimes[start], np.ones(len(start)), 'bv')
    #         plt.plot(spiketimes[end], np.ones(len(end)), 'g^')
    #         plt.show()
    #         plt.close()


# 
# scratch_spike_analysis.py ends here
