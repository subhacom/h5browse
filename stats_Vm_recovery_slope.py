# stats_Vm_recovery_slope.py --- 
# 
# Filename: stats_Vm_recovery_slope.py
# Description: 
# Author: 
# Maintainer: 
# Created: Fri Nov 30 13:26:10 2012 (+0530)
# Version: 
# Last-Updated: Fri Nov 30 16:20:30 2012 (+0530)
#           By: subha
#     Update #: 121
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# http://magaj.ncbs.res.in/notepal2012/blogs/subha/2012-11-28
# 
# This script is for statistics of the slope of Vm recovery with
# change in number of deepbasket cells

# Change log:
# 
# 
# 
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.
# 
# 

# Code:

import sys
import os
import numpy as np
from collections import defaultdict
from operator import itemgetter
import matplotlib
matplotlib.use('GTKAgg')
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt
from matplotlib._pylab_helpers import Gcf

sys.path.append(os.path.expanduser('~/src/dataviz'))

from traubdata import TraubData, cellcount_tuple
from analyze_excitation_inhibition_balance import get_spiking_cell_counts
from get_files_by_ts import load_celltype_colors


files = ['/data/subha/rsync_ghevar_cortical_data_clone/2012_09_19/data_20120919_172536_12276.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_09_22/data_20120922_195344_13808.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_09_25/data_20120925_140523_15171.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_09_28/data_20120928_095506_16949.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_09_29/data_20120929_184651_17981.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_10_03/data_20121003_091501_19886.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_10_04/data_20121004_201146_20645.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_10_06/data_20121006_081815_23857.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_10_08/data_20121008_104359_25161.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_10_12/data_20121012_140308_27319.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_10_14/data_20121014_184919_28619.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_05/data_20121105_144428_16400.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_07/data_20121107_100729_29479.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_08/data_20121108_210758_30357.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_12/data_20121112_112211_685.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_14/data_20121114_091030_2716.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_16/data_20121116_091100_3774.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_18/data_20121118_132702_5610.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_20/data_20121120_090612_6590.h5',
         '/data/subha/rsync_ghevar_cortical_data_clone/2012_11_22/data_20121122_145449_8016.h5']

def vm_recovery_stats(files, celltype, mincount=3, maxisi=25e-3):
    datalist = [TraubData(filename) for filename in files]
    deepbasket_data_map = defaultdict(list)
    for data in datalist:
        deepbasket_data_map[data.cellcounts.DeepBasket].append(data)
    for deepbasket_count, datalist in deepbasket_data_map.items():
        for data in datalist:
            cell_list = [cell for cell in data.fdata['Vm'] if cell.startswith(celltype)]
            vm_list = [np.asarray(data.fdata['Vm'][cell]) for cell in cell_list]
            burst_dict = data.get_burst_arrays(cell_list)
            interburst_times = []
            for cell in cell_list:
                burst_array = burst_dict[cell]
                # Adding/subtracting maxisi to leave enough space for
                # the immediate vicinity of a spike
                burst_starts = np.asarray(map(itemgetter(0), burst_array)) - maxisi
                burst_ends = np.asarray(map(itemgetter(-1), burst_array)) + maxisi
                vm = np.asarray(data.fdata['Vm'][cell])
                ts = np.linspace(0, data.simtime, len(vm))
                start_indices = np.searchsorted(ts, burst_starts)
                end_indices = np.searchsorted(ts, burst_ends)
                split_indices = np.hstack(zip(start_indices, end_indices))                
                split_vm = np.array_split(vm, split_indices)                
                split_ts = np.array_split(ts, split_indices)
                interburst_vms = [split_vm[ii] for ii in range(0, len(split_indices), 2)]
                interburst_ts = [split_ts[ii] for ii in range(0, len(split_indices), 2)]                
                plt.plot(ts, vm, 'y-')
                for ibvm, ibts in zip(interburst_vms, interburst_ts):
                    plt.plot(ibts, ibvm, 'g-.')                
                plt.plot(data.spikes[cell], np.zeros(len(data.spikes[cell])), 'r|', alpha=0.7)
                break
            break
        break
    plt.show()

if __name__ == '__main__':
    vm_recovery_stats(files, 'SpinyStellate')
            

# 
# stats_Vm_recovery_slope.py ends here
