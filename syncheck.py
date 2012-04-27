# syncheck.py --- 
# 
# Filename: syncheck.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Apr 25 10:45:32 2012 (+0530)
# Version: 
# Last-Updated: Fri Apr 27 16:57:24 2012 (+0530)
#           By: subha
#     Update #: 512
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# code to check the synaptic connectivity - i suspect i have messsed
# up again with connectivity settings. A spinystellate showed all tcr
# cells connected to it.
# 
# 

# Code:

import h5py as h5
import numpy as np
from matplotlib import pyplot as plt
import igraph as ig
import subprocess

celltype_color_dict = {
    'SupPyrRS': 'black',
    'SupPyrFRB': 'gray',
    'SupBasket': 'maroon',
    'SupAxoaxonic': 'red',
    'SupLTS': 'purple',
    'SpinyStellate': 'fuchsia',
    'TuftedIB': 'green',
    'TuftedRS': 'lime',
    'NontuftedRS': 'olive',
    'DeepBasket': 'yellow',
    'DeepAxoaxonic': 'navy',
    'DeepLTS': 'blue',
    'TCR': 'teal',
    'nRT': 'aqua' }

def normalize(data):
    if max(data) == min(data):
        return data
    return (data  - min(data))/(max(data) - min(data))

class SynAnalyzer(object):
    def __init__(self, datafilepath):
        netfilepath = datafilepath.replace('/data_', '/network_') + '.new'
        self.datafile = h5.File(datafilepath, 'r')
        self.netfile = h5.File(netfilepath, 'r')
        self.simdt = 1.0
        self.plotdt = 1.0
        self.simtime = 10.0
        for row in self.datafile['runconfig/scheduling'][:]:
            if row[0] == 'simdt':
                self.simdt = float(row[1])
            elif row[0] == 'plotdt':
                self.plotdt = float(row[1])
            elif row[0] == 'simtime':
                self.simtime = float(row[1])
        self.syntab = self.netfile['/network/synapse']
        self.istart = 0
        self.iend = -1

    def __del__(self):
        self.netfile.close()
        self.datafile.close()

    def select_syninfo(self, cellname, srctype, syntype):
        """Return a view containing the presynaptic cells of `cellname` of
        type `srctype` with synapses of `syntype`"""
        idx = np.char.startswith(self.syntab['dest'], cellname) & \
            np.char.startswith(self.syntab['source'], srctype) & \
            np.char.startswith(self.syntab['type'], syntype)
        return self.syntab[idx]

    def get_normalized_gk_slice(self, postcell, pretype, syntype):
        gkpath = 'gk_%s_%s_from_%s' % (postcell, syntype, pretype)
        gk = []
        try:
            gk = np.asarray(self.datafile['/synapse/'+gkpath])
            gk = normalize(gk)[self.istart:self.iend]
        except KeyError:
            print 'No synaptic Gk for', gkpath
        return gk
    
    def plot_presynaptic(self, cellname, 
                         srctype, 
                         syntype):
        syntab = self.select_syninfo(cellname, srctype, syntype)
        print syntab
        precells = [item[0] for item in np.char.split(syntab['source'], '/')]
        unique_precells = list(set(precells))
        syntypes = ['gaba', 'ampa', 'nmda']
        lstyles = {'gaba':'-.', 'ampa':'--', 'nmda':':'}
        # If specified `syntype` is not empty string, it is the only one
        # to be looked at
        for ii in range(len(unique_precells)):
            print 'Presynaptic cell:', precells[ii]
            pretype = unique_precells[ii].split('_')[0]
            try:
                vm = np.asarray(self.datafile['/Vm/'+ unique_precells[ii]])
                print min(vm), max(vm)
                vm = normalize(vm)[self.istart:self.iend]
                print min(vm), max(vm)
                # Shift the normalize plots around 0 so all of them don't
                # overlap with the original
                l2d = plt.plot(self.tseries, 
                               vm - ii - 1,
                               label=unique_precells[ii])
            except KeyError:
                print 'No Vm for', unique_precells[ii]
                continue            
            try:
                jj = -1
                while True:
                    jj = precells.index(unique_precells[ii], jj+1)
                    gk = self.get_normalized_gk_slice(
                        syntab['dest'][jj].replace('/', '_'),
                        pretype,
                        syntab['type'][jj])
                    if len(gk) == 0:
                        continue
                    plt.plot(self.tseries,
                             gk - ii - 1,
                             color=l2d[0].get_color(),
                             ls=lstyles[syntab['type'][jj]],
                             label='%s:%s<-%s' % (syntab['type'][jj], 
                                                  syntab['dest'][jj].split('/')[0], 
                                                  pretype))
            except ValueError:
                pass
        return unique_precells

    def plot_traces(self, cellname, targettime, historytime, srctype, syntype):
        """Plot traces of presynaptic data for cellname for `historytime`
        around `targettime`."""
        self.tstart = targettime - historytime
        self.istart = int(self.tstart / self.plotdt + 0.5)
        self.tend = targettime + historytime
        self.iend = int(self.tend / self.plotdt + 0.5)
        self.tseries = np.linspace(self.tstart, self.tend, 
                                 self.iend - self.istart)
        vm = self.datafile['/Vm/' + cellname]        
        plt.plot(self.tseries, 
                 normalize(vm[self.istart:self.iend]),
                 label=cellname)
        stimdata = np.asarray(self.datafile['/stimulus/stim_bg'])
        stim_start = int(self.tstart/self.simdt+0.5)
        stim_end = int(self.tend/self.simdt+0.5)
        stimdata = stimdata[stim_start: stim_end]
        plt.plot(np.linspace(self.tstart, self.tend, len(stimdata)),
                 normalize(stimdata),
                 'r--',                 
                 label='STIMULUS')
        precells = self.plot_presynaptic(cellname, srctype, syntype)
        return precells

    def get_peak_Vm_time(self, cellname, tstart, tend):
        """Return the time of the peak value for Vm of this cell"""
        istart = int(tstart/self.plotdt+0.5)
        iend = int(tend/self.plotdt+0.5)
        data = self.datafile['/Vm/'+cellname][istart:iend]
        peakindex = data.argmax()
        peaktime = tstart + peakindex * self.plotdt
        print 'peak time:', cellname, ':', peaktime
        return peaktime
        
if __name__ == '__main__':
    dfname = '/data/subha/cortical/py/data/2012_04_24/data_20120424_145719_7507.h5'
    synan = SynAnalyzer(dfname)
    targettime = 7.0
    contexttime = 0.05
    targetcell = 'SpinyStellate_0'
    precells = []
    done_cells = set(['SpinyStellate_0'])
    plt.clf()
    pre = synan.plot_traces('SpinyStellate_0', 
                            targettime,
                            contexttime,
                            '',
                            '')
    precells.append(pre)
    plt.legend()
    plt.setp(plt.gca().get_legend().get_texts(), fontsize='small')
    mgr = plt.get_current_fig_manager()
    # if mgr.__class__.__name__.endswith('GTKAgg'):
    #     mgr.full_screen_toggle()
    plt.show()
    while precells:        
        old_targettime = targettime
        for precell in precells.pop(0):
            if precell in done_cells:
                continue
            done_cells.add(precell)
            targettime = synan.get_peak_Vm_time(precell, 
                                                old_targettime-contexttime, 
                                                old_targettime+contexttime)
            pre = synan.plot_traces(precell,
                                    targettime,
                                    contexttime,
                                    '',
                                    '')
            precells.append(pre)
            plt.legend()
            plt.setp(plt.gca().get_legend().get_texts(), fontsize='small')
            mgr = plt.get_current_fig_manager()
            # if mgr.__class__.__name__.endswith('GTKAgg'):
            #     mgr.full_screen_toggle()
            plt.show()
        old_targettime -= contexttime
        if old_targettime < 0:
            break

    # nfname = '/data/subha/cortical/py/data/2012_04_24/network_20120424_145719_7507.h5.new'
    # cellname = 'SpinyStellate_21'
    # sourcetype = ''#'TCR'
    # synapsetype = 'nmda'
    # df = h5.File(dfname, 'r')
    # nf = h5.File(nfname, 'r')
    # plotdt = 1.0
    # simdt = 1.0
    # simtime = 10.0
    # for row in df['runconfig/scheduling'][:]:
    #     if row[0] == 'simdt':
    #         simdt = float(row[1])
    #     elif row[0] == 'plotdt':
    #         plotdt = float(row[1])
    #     elif row[0] == 'simtime':
    #         simtime = float(row[1])
    # vm = df['/Vm/'+cellname][:]
    # vm = normalize(vm)
    # plt.plot(np.linspace(0, simtime, len(vm)), 
    #          vm, 
    #          color=celltype_color_dict[cellname.split('_')[0]], 
    #          ls=':',
    #          label=cellname)
    # tstart = 6.0
    # tend = 7.5
    # plot_presynaptic(cellname, sourcetype, synapsetype, nf, df, tstart, tend)
    # plt.legend(loc='lower left')
    # plt.show()

# 
# syncheck.py ends here
