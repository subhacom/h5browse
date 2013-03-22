# plot_period_variability.py --- 
# 
# Filename: plot_period_variability.py
# Description: 
# Author: 
# Maintainer: 
# Created: Mon Feb 18 18:04:02 2013 (+0530)
# Version: 
# Last-Updated: Thu Mar 21 16:41:54 2013 (+0530)
#           By: subha
#     Update #: 787
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# This is to plot the variability of periodic synchronized activity.
# 
# 

# Change log:
# 
# 
# 
# 

# Code:
import os
import numpy as np
import sys
sys.path.append('/home/subha/src/dataviz')
from util import *
import peakdetect as pd
from matplotlib import gridspec as gs
from statsmodels.graphics import boxplots as bp
from traubdata import TraubData

def dft_spiketime_histogram(data):
    """Calculate the DFT of spike time histogram."""
    pass

def plot_period_variability(datalist):
    """Plot the variability of the periodicity of the data with
    increase in number of basket cells."""
    pass

def calculate_spiketime_histogram(data, timerange=(0,1e9), plotdt=25e-3):
    """Calculate the population spike time histogram in the data. Data
    is recorded at 1/plotdt sampling rate.
    
    Parameters
    
    data: a list of arrays of spike trains

    timerange: tuple(start, end) time range to consider.

    plotdt: interval between successive sampling
    """
    bins = np.arange(timerange[0], timerange[1]+plotdt, plotdt) # Adding plotdt to the end attempts to make the bins list end with timerange[1]
    merged = np.concatenate(data) # Put all the spike trains together as a single train
    return np.histogram(merged, bins)

def syncspike_peaks(hist, bins, cutoff=0.2):
    """Compute locations of the peaks in hist which are at least > cutoff.

    Returns
    List of bins and histogram values at the peaks.

    """
    x = bins[:-1] + 0.5*(bins[1] - bins[0])
    crests, troughs = pd.peakdetect(hist, x_axis=x, lookahead=10)
    if len(crests) > 0:
        x, y = zip(*crests)
        x = np.asarray(x)
        y = np.asarray(y)
        idx = np.nonzero(y > cutoff)[0]
        return (x[idx].copy(), y[idx].copy())
    return ([], [])

    
dbcnt_fname = {
    30: ('data_20120919_172536_12276.h5',
         'data_20120922_195344_13808.h5',
         'data_20120925_140523_15171.h5',
         'data_20120928_095506_16949.h5',
         'data_20120929_184651_17981.h5'
         ),
    40: ('data_20121003_091501_19886.h5',
         'data_20121004_201146_20645.h5',
         'data_20121006_081815_23857.h5',
         'data_20121008_104359_25161.h5',
         'data_20121012_140308_27319.h5'),
    50: ('data_20121014_184919_28619.h5',
         'data_20121105_144428_16400.h5',
         'data_20121107_100729_29479.h5',
         'data_20121108_210758_30357.h5',
         'data_20121112_112211_685.h5'),
    60: ('data_20121114_091030_2716.h5',
         'data_20121116_091100_3774.h5',
         'data_20121118_132702_5610.h5',
         'data_20121120_090612_6590.h5',
         'data_20121122_145449_8016.h5')
    }

from matplotlib import pyplot as plt

datadir = '/data/subha/rsync_ghevar_cortical_data_clone'

def plot_histograms(histdict):
    """Draw line plots joining the number of cells spiking in each
    bin.

    One figure for each set.

    One axis for each simulation.

    """
    for count in sorted(dbcnt_fname.keys()):
        fig = plt.figure(count)    
        fig.suptitle('deepbasket cells: %d' % (count))
        ax = None
        for index, fname in enumerate(dbcnt_fname[count]):
            ax = fig.add_subplot(len(dbcnt_fname[count]), 1, index+1, sharex=ax, sharey=ax)
            hist, bins = histdict[fname]
            ax.plot(bins[:-1]+0.5*(bins[1] - bins[0]), hist)        
    # plt.show()

from itertools import *

def get_spiking_cell_hist(celltype, trange=(0,1e9), binsize=5e-3):
    ret = {}
    for fname in chain(*dbcnt_fname.values()):
        print fname
        data = TraubData(makepath(fname))
        hist, bins = data.get_spiking_cell_hist(celltype, timerange=trange, binsize=binsize)
        ncell = data.cellcounts._asdict()[celltype]
        hist /= 1.0 * ncell
        ret[fname] = (hist, bins)
    return ret

import copy
from matplotlib.colors import LogNorm
from matplotlib.backends.backend_pdf import PdfPages
# This is for colorbar with tightlayout. See:
# http://matplotlib.org/users/tight_layout_guide.html
from mpl_toolkits.axes_grid1 import make_axes_locatable 

def plot_colormapped(histdict, lognorm=False, pdf=None, cmap=plt.cm.jet):
    """Plot the histograms in a heatmap.

    Parameters:

    histdict: dictionary mapping filename to (histogram, bins)
    [i.e. the output of numpy.hist()]

    lognorm: if True use LogNorm for colormap (the colorscale will be
    logarithmic instead of linear).

    pdf: filename for PDF output. If None (default) only on screen
    display will be done.

    cmap: colormap to use    

    """
    cmap = copy.copy(cmap)
    cmap.set_bad((0, 0, 0)) # For log-normalized plot the 0 values
                            # will be treated as bad. Make them black
                            # or the lower end of the colormap.
    ax = None
    norm = None
    if lognorm:
        norm = LogNorm()
    fig = plt.figure()
    for index, count in enumerate(sorted(dbcnt_fname.keys())):
        ax = fig.add_subplot(len(dbcnt_fname), 1, index+1)
        ax.set_title('deepbaskets: %d' % (count))
        x, yvalues = None, []
        for fname in dbcnt_fname[count]:
            hist, bins = histdict[fname]
            x = bins #bins[:-1] + 0.5 * (bins[1] - bins[0])
            yvalues.append(hist)        
        Z = np.vstack(yvalues)
        y = np.arange(len(yvalues)+1.0)
        X, Y = np.meshgrid(x, y)
        # ax.pcolormesh(x, y, z)
        print X.shape, Y.shape, Z.shape
        img = ax.pcolormesh(X, Y, Z, norm=norm, cmap=cmap)
        # The divider is to include the colorbar into tight_layout.
        # divider = make_axes_locatable(ax)
        # cax = divider.append_axes('right', '2%', pad='0.5%')        
        # fig.colorbar(img, cax=cax)
        fig.colorbar(img, ax=ax, use_gridspec=True, pad=0.01, aspect=10, ticks=np.arange(0,1.2, 0.2))
    ax.set_xlabel('Time (s)')
    plt.tight_layout()
    if pdf is not None:
        pdfout = PdfPages(pdf)
        pdfout.savefig()
        pdfout.close()
        plt.savefig(pdf.replace('pdf', 'png'))
    # plt.show()

def plot_syncspike_peaks(histdict):
    """Plot the peaks in synchronously spiking fraction of cells in
    all the histograms in histdict.

    histdict: filename: (hist, bins) dictionary

    """
    for count in sorted(dbcnt_fname.keys()):
        fig = plt.figure(count)    
        fig.suptitle('deepbasket cells: %d' % (count))
        ax = None
        for index, fname in enumerate(dbcnt_fname[count]):
            ax = fig.add_subplot(len(dbcnt_fname[count]), 1, index+1, sharex=ax, sharey=ax)
            hist, bins = histdict[fname]            
            ax.plot(bins[:-1]+0.5*(bins[1] - bins[0]), hist)        
            x, y = syncspike_peaks(hist, bins)
            ax.plot(x, y, 'rd')
    # plt.show()

def plot_syncspike_peaks_stats(histdict, cutoff=0.2, mode=None, pdf=None):
    fig = plt.figure()
    grid = gs.GridSpec(4,4)
    ax = None
    ax1 = None
    for index, count in enumerate(sorted(dbcnt_fname.keys())):
        ax = fig.add_subplot(grid[index, :-1], sharex=ax, sharey=ax)
        ax.set_title('deepbaskets: %d' % (count))
        data = []
        for fname in dbcnt_fname[count]:
            hist, bins = histdict[fname]
            x, y = syncspike_peaks(hist, bins, cutoff=cutoff)
            data.append((np.mean(y), np.std(y)))
        print data
        ax1 = fig.add_subplot(grid[index, -1], sharex=ax1, sharey=ax)
        if mode == 'bar':
            ax.bar(np.arange(1, 6, 1.0), [d[0] for d in data], yerr=[d[1] for d in data], width=0.4, color='gray', lw=0, error_kw={'ecolor':'k'})
            ax1.bar([0.3], [np.mean([d[0] for d in data])], yerr=[np.std([d[0] for d in data])], color='gray', width=0.4, lw=0, error_kw={'ecolor':'k'})
        else:
            ax.errorbar(np.arange(1, 6, 1.0), [d[0] for d in data], yerr=[d[1] for d in data], fmt='o', ls='-', lw=0)
            ax1.errorbar([1.0], [np.mean([d[0] for d in data])], yerr=[np.std([d[0] for d in data])], fmt='o', ls='-', lw=0)            
        ax.xaxis.set_visible(False)
        ax1.xaxis.set_visible(False)
        ax1.yaxis.set_visible(False)
    yt = np.arange(0, 1.3, 0.2)
    ax1.set_yticks(yt)
    ax1.set_xlim(left=0, right=1)
    txt = fig.text(0.0, 0.0, 'Fraction of cells spiking synchronously',
                   rotation='vertical',
                   horizontalalignment='left', 
                   verticalalignment='bottom')
    txt.set_transform(fig.transFigure)
    txt.set_position((0.01, 0.1))
    fig.subplots_adjust(left=0.1)
    fig.tight_layout(pad=2.0)
    if pdf is not None:
        pdfout = PdfPages(pdf)
        pdfout.savefig()
        pdfout.close()
        plt.savefig(pdf.replace('pdf', 'png'))

def plot_syncspike_period_stats(histdict, cutoff=0.2, mode=None, pdf=None):
    fig = plt.figure()
    grid = gs.GridSpec(4,4)
    ax = None
    ax1 = None
    for index, count in enumerate(sorted(dbcnt_fname.keys())):
        ax = fig.add_subplot(grid[index, :-1], sharex=ax, sharey=ax)
        ax.set_title('deepbaskets: %d' % (count))
        data = []
        for fname in dbcnt_fname[count]:
            hist, bins = histdict[fname]
            x, y = syncspike_peaks(hist, bins, cutoff=cutoff)
            intervals = np.diff(x)
            data.append((np.mean(intervals), np.std(intervals)))
        print data
        ax1 = fig.add_subplot(grid[index, -1], sharex=ax1, sharey=ax)
        if mode == 'bar':
            ax.bar(np.arange(1, 6, 1.0), [d[0] for d in data], yerr=[d[1] for d in data], width=0.4, color='gray', lw=0, error_kw={'ecolor':'k'})
            ax1.bar([0.3], [np.mean([d[0] for d in data])], yerr=[np.std([d[0] for d in data])], width=0.4,color='gray', lw=0, error_kw={'ecolor':'k'})
        else:
            ax.errorbar(np.arange(1, 6, 1.0), [d[0] for d in data], yerr=[d[1] for d in data])            
            ax1.errorbar([1.0], [np.mean([d[0] for d in data])], yerr=[np.std([d[0] for d in data])])
        ax.xaxis.set_visible(False)
        ax1.xaxis.set_visible(False)
        ax1.yaxis.set_visible(False)
    yt = np.arange(0, 1.0, 0.2)
    ax1.set_yticks(yt)
    ax1.set_xlim(left=0, right=1)
    txt = fig.text(0.0, 0.0, 'Interval between synchronized spiking (s)', 
                   rotation='vertical',
                   horizontalalignment='left', 
                   verticalalignment='bottom')
    txt.set_transform(fig.transFigure)
    txt.set_position((0.01, 0.1))
    fig.subplots_adjust(left=0.1)
    fig.tight_layout(pad=2.0)
    if pdf is not None:
        pdfout = PdfPages(pdf)
        pdfout.savefig()
        pdfout.close()
        plt.savefig(pdf.replace('pdf', 'png'))

def boxplot_syncspike_peaks(histdict, cutoff=0.2, pdf=None):
    fig = plt.figure()
    grid = gs.GridSpec(4,4)
    ax = None
    ax1 = None
    for index, count in enumerate(sorted(dbcnt_fname.keys())):
        ax = fig.add_subplot(grid[index, :-1], sharex=ax, sharey=ax)
        ax.set_title('deepbaskets: %d' % (count))
        data = []
        for fname in dbcnt_fname[count]:
            hist, bins = histdict[fname]
            x, y = syncspike_peaks(hist, bins, cutoff=cutoff)
            data.append(y)
        ax.boxplot(data)
        ax.xaxis.set_visible(False)
        ax1 = fig.add_subplot(grid[index, -1], sharex=ax1, sharey=ax)
        ax1.boxplot([np.mean(d) for d in data])
        ax1.xaxis.set_visible(False)
        ax1.yaxis.set_visible(False)
    yt = np.arange(0, 1.2, 0.2)
    ax1.set_yticks(yt)
    txt = fig.text(0.0, 0.0, 'Fraction of cells spiking synchronously', 
                   rotation='vertical',
                   horizontalalignment='left', 
                   verticalalignment='bottom')
    txt.set_transform(fig.transFigure)
    txt.set_position((0.01, 0.1))
    fig.subplots_adjust(left=0.1)
    fig.tight_layout(pad=2.0)
    if pdf is not None:
        pdfout = PdfPages(pdf)
        pdfout.savefig()
        pdfout.close()
        plt.savefig(pdf.replace('pdf', 'png'))
    # plt.show()

def boxplot_syncspike_period(histdict, cutoff=0.2, pdf=None):
    fig = plt.figure()
    grid = gs.GridSpec(4,4)
    ax = None
    ax1 = None
    for index, count in enumerate(sorted(dbcnt_fname.keys())):
        ax = fig.add_subplot(grid[index, :-1], sharex=ax, sharey=ax)
        ax.set_title('deepbaskets: %d' % (count))
        data = []
        for fname in dbcnt_fname[count]:
            hist, bins = histdict[fname]
            x, y = syncspike_peaks(hist, bins, cutoff=cutoff)
            data.append(np.diff(x))
        ax.boxplot(data)
        ax.xaxis.set_visible(False)
        ax1 = fig.add_subplot(grid[index, -1], sharex=ax1, sharey=ax)
        ax1.boxplot([np.mean(d) for d in data])
        ax1.xaxis.set_visible(False)
        ax1.yaxis.set_visible(False)
    yt = np.arange(0, 1.0, 0.2)
    ax1.set_yticks(yt)
    txt = fig.text(.01, .1, 'Interval between synchronized spiking (s)', 
              rotation='vertical',
              horizontalalignment='left', 
              verticalalignment='bottom')
    txt.set_transform(fig.transFigure)
    txt.set_position((0.01, 0.1))
    fig.subplots_adjust(left=0.1)
    fig.tight_layout(pad=2)
    if pdf is not None:
        pdfout = PdfPages(pdf)
        pdfout.savefig()
        pdfout.close()
        plt.savefig(pdf.replace('pdf', 'png'))
    # plt.show()

def plot_sync_cell_distribution(histdict):    
    columns = len(dbcnt_fname)
    rows = 5
    fig = plt.figure()
    index = 0
    for count in sorted(dbcnt_fname.keys()):
        for fname in dbcnt_fname[count]:
            index += 1
            ax = fig.add_subplot(rows, columns, index)
            ax.set_title(fname)
            binsize=0.1
            ax.hist(histdict[fname][0], bins=np.arange(0, 1+binsize, binsize))
    # plt.show()

if __name__ == '__main__':
    histdict = get_spiking_cell_hist('SpinyStellate', trange=(10, 12.0))
    # plot_colormapped(histdict, pdf='../images/syncspikefracss.pdf')
    # histdict = get_spiking_cell_hist('DeepBasket', trange=(10.0, 12.0))
    # plot_colormapped(histdict, pdf='../images/syncspikefracdb.pdf')
    # histdict = get_spiking_cell_hist('DeepLTS', trange=(10.0, 12.0))
    # plot_colormapped(histdict, pdf='../images/syncspikefracdlts.pdf')
    # plot_syncspike_peaks(histdict)
    # boxplot_syncspike_period(histdict, cutoff=0.1, pdf='../images/ssperiodboxplot.pdf')
    # boxplot_syncspike_peaks(histdict, cutoff=0.1, pdf='../images/ssfracboxplot.pdf')
    # plot_sync_cell_distribution(histdict)
    plot_syncspike_peaks_stats(histdict, cutoff=0.1, mode='bar', pdf='../images/ssfracbarplot.pdf')
    plot_syncspike_period_stats(histdict, cutoff=0.1, mode='bar', pdf='../images/ssperiodbarplot.pdf')
    plt.show()

# 
# plot_period_variability.py ends here
