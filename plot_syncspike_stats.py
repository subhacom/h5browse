# plot_variability_with_GABA.py --- 
# 
# Filename: plot_variability_with_GABA.py
# Description: 
# Author: 
# Maintainer: 
# Created: Thu Mar 14 15:26:03 2013 (+0530)
# Version: 
# Last-Updated: Thu Mar 21 17:26:42 2013 (+0530)
#           By: subha
#     Update #: 373
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
"""Plot the variability of synchronized spiking with increase in GABA
conductance"""

import sys
import os
sys.path.append('/home/subha/src/dataviz')
from traubdata import TraubData
from get_files_by_ts import find_files, get_fname_timestamps, get_files_by_ts
from util import get_celltype_colors
from plot_period_variability import makepath, get_spiking_cell_hist, plot_colormapped
from matplotlib import rc, rcParams
from matplotlib import pyplot as plt
import numpy as np

from matplotlib.backends.backend_pdf import PdfPages

datadir = '/data/subha/rsync_ghevar_cortical_data_clone'

current_font = {}
def enable_latex():
    global current_font
    current_font.update(rcParams)
    rc('font', **{'family':'serif','serif':['Palatino']})
    rcParams['text.latex.preamble'] = '\usepackage{siunitx}'
    rc('text', usetex=True)

def disable_latex():
    if  current_font:
        rcParams.update(current_font)

flist = set([
# These are different number of TCR cells stimulated
        'data_20120919_172536_12276.h5',
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
        'data_20121122_145449_8016.h5',
        # 'data_20121114_091030_2716.h5', ## This is the network template for the rest
        # 'data_20130220_133500_24268.h5',
        # 'data_20130225_151150_27463.h5',
        # 'data_20130222_172520_25513.h5',
        # 'data_20130227_090938_28653.h5',
        # 'data_20130318_085236_2590.h5',
        # 'data_20130319_205710_3880.h5',
        # 'data_20130301_101425_29754.h5',
        # 'data_20130303_153540_31841.h5',
        ])


def get_mean_gbar(data, syntype, pretype, posttype):
    syn = data.synapse[(data.synapse['type'] == syntype) & np.char.startswith(data.synapse['source'], pretype) & np.char.startswith(data.synapse['dest'], posttype)].copy()
    # print syn
    return np.mean(syn['Gbar'])

import operator
from plot_period_variability import syncspike_peaks
    
def plot_hist(datalist):
    histdict = {}
    gaba_dict = {}
    for d in datalist:
        gaba_dict[d] = get_mean_gbar(d, 'gaba', 'DeepBasket', 'SpinyStellate')
    for d in datalist:
        histdict[d] =  d.get_spiking_cell_hist('SpinyStellate', timerange=(1.0, 20.0), frac=True)        
    for k, v in gaba_dict.items():
        print k.fdata.filename, v
    ax = None    
    # enable_latex()
    for index, (d, gaba) in enumerate(sorted(gaba_dict.iteritems(), key=operator.itemgetter(1))):
        if index % 4 == 0:
            fig = plt.figure()
        ax = fig.add_subplot(4, 1, index%4+1, sharex=ax, sharey=ax)
        # ax.text(8.0, 0.8, '$\displaystyle\overline{G}_{GABA} = %.2f$ nS' % (gaba_dict[d]/1e-9))
        ax.text(10.0, 1.0, 'DB: %d, $\overline{G}_{GABA} = %.2f$ nS' % (d.cellcounts.DeepBasket, gaba_dict[d]/1e-9))
        x, yvalues = None, []
        hist, bins = histdict[d]
        x = bins[:-1] + 0.5 * (bins[1] - bins[0])
        plt.plot(x, hist, '-')        
        ax.yaxis.tick_left()
        ax.xaxis.set_visible(False)
        plt.setp(ax, frame_on=False)
        ax.set_ylim((0.0, 1.2))
    ax.set_xlabel('Time (s)')
    ax.set_yticks([0.0, 0.5, 1.0])
    ax.xaxis.set_visible(True)
    ax.xaxis.tick_bottom()
    plt.tight_layout()
    pdfout = PdfPages('syncspikehistswithgaba.pdf')
    pdfout.savefig()
    pdfout.close()
    plt.show()
    # disable_latex()
    return histdict, gaba_dict

def boxplot_period_stats(hdict, gabadict, cutoff=0.2):
    plotdata = []
    width = 0.4
    indices = np.arange(len(hdict))
    xlabels = []
    for index, (data, gaba) in enumerate(sorted(gaba_dict.iteritems(), key=operator.itemgetter(1))):
        hist, bins = hdict[data]
        x, y = syncspike_peaks(hist, bins, cutoff=cutoff)
        # plt.plot(bins[:-1]+bins[1]-bins[0], hist)
        # plt.plot(x, y, 'rx')
        # plt.title(data.fdata.filename)
        # plt.show()
        intervals = np.diff(x)
        plotdata.append((np.mean(intervals), np.std(intervals)))
        xlabels.append('%0.1fx' % (gaba/2.5e-9))
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.bar(indices, [d[0] for d in plotdata], yerr=[d[1] for d in plotdata], width=0.4, color='gray', lw=0, error_kw={'ecolor':'k'})
    ax.set_xticks(indices + width/2)
    ax.set_xticklabels(xlabels)
    ax.set_xlabel('Peak conductance of GABA synapses compared to baseline')
    ax.set_ylabel('Interval between synchronized firing (s)')
    # ax.xaxis.set_visible(False)
    # ax.yaxis.set_visible(False)
    plt.setp(ax, frame_on=False)
    yticks = np.arange(0, 0.5, 0.1)
    ax.set_yticks(yticks)
    ax.xaxis.tick_bottom()
    ax.yaxis.tick_left()
    pdfout = PdfPages('ssperiodwithgaba.pdf')
    pdfout.savefig()
    pdfout.close()
    plt.show()

def boxplot_peaks_stats(hdict, gabadict, cutoff=0.2):
    plotdata = []
    xlabels = []
    for index, (data, gaba) in enumerate(sorted(gaba_dict.iteritems(), key=operator.itemgetter(1))):
        hist, bins = hdict[data]
        x, y = syncspike_peaks(hist, bins, cutoff=cutoff)
        # plt.plot(bins[:-1]+bins[1]-bins[0], hist)
        # plt.plot(x, y, 'rx')
        # plt.title(data.fdata.filename)
        # plt.show()
        plotdata.append((np.mean(y), np.std(y)))
        xlabels.append('%1.1fx' % (gaba/2.5e-9))    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    indices = np.arange(len(hdict))
    width = 0.4
    ax.bar(indices, [d[0] for d in plotdata], width=width, yerr=[d[1] for d in plotdata], color='gray', lw=0, error_kw={'ecolor':'k'})
    ax.set_xticks(indices + width/2)
    ax.set_xticklabels(xlabels)
    ax.set_xlabel('Peak conductance of GABA synapses compared to baseline')
    ax.set_ylabel('Fraction of cells spiking synchronously')
    # ax.xaxis.set_visible(False)
    # ax.yaxis.set_visible(False)
    plt.setp(ax, frame_on=False)
    ax.set_yticks([0, 0.5, 1])
    ax.set_ylim((0, 1.0))
    ax.xaxis.tick_bottom()
    ax.yaxis.tick_left()
    pdfout = PdfPages('ssfracwithgaba.pdf')
    pdfout.savefig()
    pdfout.close()
    plt.show()
    
    
if __name__ == '__main__':
    files = [makepath(f, datadir) for f in flist]
    datalist = [TraubData(fname) for fname in files]
    hdict, gaba_dict, = plot_hist(datalist)
    boxplot_peaks_stats(hdict, gaba_dict, cutoff=0.1)
    boxplot_period_stats(hdict, gaba_dict, cutoff=0.1)

# 
# plot_variability_with_GABA.py ends here
