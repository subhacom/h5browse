import os
import numpy as np
import sys
sys.path.append('/home/subha/src/dataviz')
from util import *
import peakdetect as pd
from matplotlib import gridspec as gs
from statsmodels.graphics import boxplots as bp
from traubdata import TraubData
from matplotlib import pyplot as plt

# Simulations with 50 deep basket cells and normal distribution of AMPA and GABA with std=100%. DeepLTS only 10.
# sd_Em was 0.01
normal_distr_db50_sd100pc = [
    'data_20130603_151249_13824.h5',
    'data_20130604_130038_14430.h5',
    'data_20130606_214805_16457.h5',
    'data_20130607_184007_17341.h5',
    'data_20130611_164312_19342.h5',]

# Simulations with 30 deep basket cells and normal distribution of AMPA, NMDA and GABA with std=1%. DeepLTS  30.
# sd_Em was 0.0
normal_distr_db30_sd001pc = [
    'data_20130926_175557_23146.h5',
    'data_20130927_130032_23546.h5',
    'data_20130928_080248_24083.h5',
    'data_20130929_030046_24339.h5',
    'data_20130929_220020_24746.h5',
    'data_20130930_165908_25439.h5',
    'data_20131001_135346_28969.h5',
    'data_20131002_085713_29287.h5',
    'data_20131003_145246_30810.h5',
    'data_20131004_121723_31136.h5',
    'data_20131005_094752_31458.h5',
    'data_20131006_072246_31658.h5',
    'data_20131007_045415_31995.h5',
    'data_20131008_022708_32336.h5',
]

# This one has 30 axoaxonic cells and sd_Em = 0.05
normal_distr_db30_aa30_sd100pc = [
    'data_20140228_103300_20533.h5']

# sd_Em = 0.05
normal_distr_db40_aa30_sd100pc = [
    'data_20140301_171224_21051.h5']

lognorm_distr_db50_sd100pc = [
    'data_20131014_153702_15212.h5',
    'data_20131015_205657_16289.h5',
    'data_20131017_091142_17255.h5',
    'data_20131018_092637_17874.h5',
    'data_20131019_180749_18739.h5',
    'data_20131020_141729_19409.h5',]

fixed_db30 = [
    'data_20130703_154757_1190.h5',
    'data_20130704_164858_1997.h5',
    'data_20130706_184225_2488.h5',
    'data_20130708_111436_3606.h5',
    'data_20130709_091028_4120.h5',]
    
def plot_spike_raster(fname, color, label):
    data = TraubData(makepath(fname))
    fig = plt.figure()
    ax = fig.add_subplot(111)
    cells = sorted(data.spikes.keys())
    for ii, cell in enumerate(cells):
        ax.plot(data.spikes[cell], np.ones(len(data.spikes[cell])) * ii + 1, ls='', marker='|', mec=color)
        ax.xaxis.set_label(label)
        ax.set_title(fname)

if __name__ == '__main__':
    cdict = get_celltype_colors()
    for fname in normal_distr_db50_sd100pc:
        plot_spike_raster(fname, 'b', 'Normal, DB=50, SD=100%') # only on stim
    for fname in normal_distr_db30_sd001pc:
        plot_spike_raster(fname, 'r', 'Normal, DB=30, SD=1%') # only on stim
    for fname in normal_distr_db30_aa30_sd100pc:
        plot_spike_raster(fname, 'g', 'Normal, DB=30, AA=30, SD=100%') # spontan bursts
    for fname in normal_distr_db40_aa30_sd100pc:
        plot_spike_raster(fname, 'k', 'Normal, DB=30, AA=40, SD=100%') # spontan bursts
    for fname in lognorm_distr_db50_sd100pc:
        plot_spike_raster(fname, 'c', 'Lognormal, DB=50, AA=40, SD=100%') # spontan bursts
    for fname in fixed_db30:
        plot_spike_raster(fname, 'orange', 'Lognormal, DB=50, AA=40, SD=100%') # spontan bursts
    plt.show()
