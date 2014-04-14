# plot_stimulated_tcr_with_spinstell.py
# 
# Filename: plot_G_exc_inh_balance.py
# Description: 
# Author: 
# Maintainer: 
# Created: Tue Nov 27 10:11:46 2012 (+0530)
# Version: 
# Last-Updated: Thu Mar 21 17:00:32 2013 (+0530)
#           By: subha
#     Update #: 325
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# Plot the spike times of stimulated TCR cells along with the Vm of a
# downstream spinystellate cell.
# 
# 

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
import matplotlib
matplotlib.use('GTKAgg')
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot as plt
from matplotlib._pylab_helpers import Gcf

sys.path.append(os.path.expanduser('~/src/dataviz'))

from traubdata import TraubData, cellcount_tuple
from util import *
from analyze_excitation_inhibition_balance import get_spiking_cell_counts
from util import get_celltype_colors

datadir = '/data/subha/rsync_ghevar_cortical_data_clone'


files = ['data_20120919_172536_12276.h5',
         'data_20120922_195344_13808.h5',
         'data_20120925_140523_15171.h5',
         'data_20120928_095506_16949.h5',
         'data_20120929_184651_17981.h5',
         'data_20121003_091501_19886.h5',
         'data_20121004_201146_20645.h5',
         'data_20121006_081815_23857.h5',
         'data_20121008_104359_25161.h5',
         'data_20121012_140308_27319.h5',
         'data_20121014_184919_28619.h5',
         'data_20121105_144428_16400.h5',
         'data_20121107_100729_29479.h5',
         'data_20121108_210758_30357.h5',
         'data_20121112_112211_685.h5',
         'data_20121114_091030_2716.h5',
         'data_20121116_091100_3774.h5',
         'data_20121118_132702_5610.h5',
         'data_20121120_090612_6590.h5',
         'data_20121122_145449_8016.h5']

def get_precount_cell_map(data, celltype):
    """Return a dict mapping number of stimulated presynaptic cells to
    set of such post synaptic cells. Excludes those with 0 such
    presynaptic cells."""
    precount_cell_map = defaultdict(set)
    bgcell_set = set(data.bg_cells)
    for cellname, spiketrain in data.spikes.items():
        if not cellname.startswith(celltype):
            continue
        presynaptic_set = set(data.presynaptic(cellname))
        stimulated_cells = presynaptic_set.intersection(bgcell_set)
        if len(stimulated_cells) == 0:
            continue
        precount_cell_map[len(stimulated_cells)].add(cellname)
    return precount_cell_map

def plot_high_stim_cells(timerange, files, colordict):
    datalist = [TraubData(makepath(fname)) for fname in files]
    exc = []
    inh = []
    fig = plt.figure(1)
    axlist = []
    first_axis = None
    rows = 4
    columns = 5
    for dindex, data in enumerate(datalist):        
        # if first_axis is None:
        #     first_axis = ax = fig.add_subplot(rows, columns, dindex+1)
        # else:
        #     ax = fig.add_subplot(rows, columns, dindex+1, sharex=first_axis, sharey=first_axis)
        print dindex
        ax = fig.add_subplot(rows, columns, dindex+1)
        axlist.append(ax)
        bgtimes = data.get_bgstim_times()
        bgtimes = bgtimes[(bgtimes >= timerange[0]) & (bgtimes < timerange[1])]
        ax.plot(bgtimes, -np.ones(len(bgtimes)), 'rv')
        # Get the cell downstream to maximum no. of bg-stimulated TCR
        precount_cell_map = get_precount_cell_map(data, 'SpinyStellate')
        maxcount = max(precount_cell_map.keys())
        maxcells = precount_cell_map[maxcount]
        candidate = None
        for cell in data.fdata['/Vm']:
            if cell in maxcells:
                candidate = cell
                break
        if candidate is None:
            print data.fdata.filename, 'has no spiny stellate cell with Vm recorded which has a bg-stimulated presynaptic cell'
            continue
        print candidate
        vm = np.asarray(data.fdata['/Vm'][candidate])
        ts = np.linspace(timerange[0], timerange[1], len(vm))
        ax.plot(ts, vm*1e3, 'y-', alpha=0.4, label='%s<-%d TCR' % (candidate, maxcount))
        for cindex, cell in enumerate(sorted(data.presynaptic(candidate))):
            spiketimes = data.spikes[cell]
            spiketimes = spiketimes[(spiketimes >= timerange[0]) & (spiketimes < timerange[1])]
            if len(spiketimes) == 0:
                print os.path.basename(data.fdata.filename), ':', cell, 'has no spikes'                
                continue
            marker=','
            if cell in data.bg_cells:
                marker = 'x'
                ax.plot(spiketimes, np.ones(len(spiketimes)) * cindex,
                        marker=marker, 
                        ls='',
                        mew=0,
                        color=colordict[cell.split('_')[0]], 
                        alpha=0.7, 
                        label='_no_label_')
        ax.legend()
    fig.patch.set_facecolor('white')

def plot_incoming_spikes_with_vm(timerange, files, colordict):
    datalist = [TraubData(makepath(fname)) for fname in files]
    exc = []
    inh = []
    fig = plt.figure(1)
    axlist = []
    first_axis = None
    rows = 4
    columns = 5
    for index, data in enumerate(datalist):        
        # if first_axis is None:
        #     first_axis = ax = fig.add_subplot(rows, columns, index+1)
        # else:
        #     ax = fig.add_subplot(rows, columns, index+1, sharex=first_axis, sharey=first_axis)
        ax = fig.add_subplot(rows, columns, index+1)
        ts = np.linspace(0, data.simtime, len(data.bg_stimulus))
        indices = np.nonzero((ts >= timerange[0]) & (ts < timerange[1]))[0]
        ts = ts[indices]
        bgstim = data.bg_stimulus[indices]
        indices = np.nonzero(np.diff(bgstim) > 0)[0]
        ax.plot(ts[indices], -np.ones(len(indices)), 'rv', label='stimulus (1 nA)')
        bg_cells = set(data.bg_cells)
        # Get the cell downstream to maximum no. of bg-stimulated TCR
        max_presynaptic = ('', 0)
        presynaptic_cells = set()
        stimulated_presynaptic_cells = set()
        max_pre_tcr = set()
        max_pre = set()
        cell = None
        for vnode in data.fdata['/Vm']:
            if not vnode.startswith('SpinyStellate'):
                continue
            presynaptic_cells = set(data.presynaptic(vnode))
            stimulated_presynaptic_cells = presynaptic_cells.intersection(bg_cells)            
            stimulated_presynaptic_cell_count =  len(stimulated_presynaptic_cells)
            if stimulated_presynaptic_cell_count > max_presynaptic[1]:
                max_presynaptic = (vnode, stimulated_presynaptic_cell_count)            
                max_pre_tcr = stimulated_presynaptic_cells
                max_pre = presynaptic_cells
        if max_presynaptic[1] == 0:
            print data.fdata.filename, 'has no spiny stellate cell with Vm recorded which has a bg-stimulated presynaptic cell'
            break     
        print 'Presynaptic bg stimulated cells:', max_presynaptic[0], max_pre_tcr
        vm = np.asarray(data.fdata['/Vm'][max_presynaptic[0]])
        ts = np.linspace(timerange[0], timerange[1], len(vm))
        ax.plot(ts, vm*1e3, 'y-', alpha=0.4, label='%s<-%d TCR' % max_presynaptic)
        for idx, pre in enumerate(sorted(max_pre)):
            spiketimes = data.spikes[pre]
            spiketimes = spiketimes[(spiketimes >= timerange[0]) & (spiketimes < timerange[1])]
            print len(spiketimes)
            if pre in bg_cells:
                ax.plot(spiketimes, np.ones(len(spiketimes)) * idx, 'x', color=colordict[pre.split('_')[0]], alpha=0.7, label='_no_label_')
            else:
                ax.plot(spiketimes, np.ones(len(spiketimes)) * idx, ',', mew=0, color=colordict[pre.split('_')[0]], alpha=0.7, label='_no_label_')
        # ax.set_ylim(bottom=-100)
        ax.text(12, 30, chr(ord('A')+index))
        # ax.xaxis.set_visible(False)
        # ax.set_yticks((0, 20, 40))
        # ax.set_yticks((-100, -50, 0, 50))
        axlist.append(ax)
        plt.setp(ax, frame_on=False)
    # axlist[2].set_ylabel('Total synaptic conductance (nS)')
    axlist[-1].xaxis.set_visible(True)
    axlist[-1].set_xlabel('Time (s)')
    fig.patch.set_facecolor('white')
    # plt.tight_layout()
    # pdf = PdfPages('../images/gexcinhbalance.pdf')
    # pdf.savefig()
    # pdf.close()
    # fig.set_size_inches(8, 6)
    # fig.savefig('../images/gexcinhbalance.png')

if __name__ == '__main__':
    colordict = get_celltype_colors()
    # plot_high_stim_cells((0, 20), files, colordict)
    plot_incoming_spikes_with_vm((0.0, 20.0), files, colordict)
    plt.show()

# 
# plot_stimulated_tcr_with_spinstell.py
