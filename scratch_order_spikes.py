# scratch_order_spikes.py --- 
# 
# Filename: scratch_order_spikes.py
# Description: 
# Author: 
# Maintainer: 
# Created: Fri Mar  2 11:37:38 2012 (+0530)
# Version: 
# Last-Updated: Fri Mar  2 13:07:53 2012 (+0530)
#           By: subha
#     Update #: 78
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# Try out plotting the spiketrains in order of the appearance of first
# spike after some specified time.
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

cell_color = {
    'DeepAxoaxonic': 'k',
    'DeepBasket': 'g',
    'DeepLTS': 'b',
    'TCR': 'r',
    'SpinyStellate': 'm',
    'nRT': 'y'
}
def firstspike_time(tstart, train):
    t = np.nonzero(train > tstart)[0]
    if len(t > 0):
        return train[t[0]]
    return 1e15
        
def sort_spikestrains(cell_spike_train_dict, timepoint):
    cells = cell_spike_train_dict.keys()
    def sortkey(cell):
        train = cell_spike_train_dict[cell]
        return firstspike_time(timepoint, train)
    sorted_cells = sorted(cells, key=sortkey)
    return sorted_cells

if __name__ == '__main__':
    filehandle = h5.File('../py/data/2012_02_08/data_20120208_115556_4589.h5', 'r')
    spikes = filehandle['/spikes']
    cell_spike_dict = dict([(cell, np.asarray(spikes[cell])) for cell in spikes if not cell.startswith('ectopic')])
    sorted_cells = sort_spikestrains(cell_spike_dict, 1.0)
    for ii in range(1, len(sorted_cells)+1):
        cell = sorted_cells[ii-1]
        print cell, firstspike_time(1.0, cell_spike_dict[cell])
        xdata = cell_spike_dict[cell]
        pl.plot(xdata, ii * np.ones(len(xdata)), '%s|' % (cell_color[cell.partition('_')[0]]))
    pl.yticks(range(1, len(sorted_cells)+1), sorted_cells)    
    pl.show()
    

# 
# scratch_order_spikes.py ends here
