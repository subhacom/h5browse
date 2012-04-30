# syncheck.py --- 
# 
# Filename: syncheck.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Apr 25 10:45:32 2012 (+0530)
# Version: 
# Last-Updated: Mon Apr 30 11:10:41 2012 (+0530)
#           By: subha
#     Update #: 614
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
        idx = np.char.startswith(self.syntab['dest'], cellname+'/') & \
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
        precells_with_vm = []
        shift = 1
        for ii in range(len(unique_precells)):
            print 'Presynaptic cell', ii, precells[ii]
            pretype = unique_precells[ii].split('_')[0]
            if unique_precells[ii] in self.datafile['/Vm']:
                vm = np.asarray(self.datafile['/Vm/'+ unique_precells[ii]])
                precells_with_vm.append(unique_precells[ii])
                print min(vm), max(vm)
                vm = normalize(vm)[self.istart:self.iend]
                print min(vm), max(vm)
                # Shift the normalize plots around 0 so all of them don't
                # overlap with the original
                l2d = plt.plot(self.tseries,
                               vm - shift,
                               label=unique_precells[ii])
            else:
                continue
            # Now plot the synaptic conductances
            jj = -1
            for kk in range(precells.count(unique_precells[ii])):
                # Find the index of this cell in syntab
                jj = precells.index(unique_precells[ii], jj+1)
                # The synaptic conductances are saved as
                # 'synapse/gk_cellname_compname_synapsetype_from_presynapticcelltype'            
                gk = self.get_normalized_gk_slice(
                    syntab['dest'][jj].replace('/', '_'),
                    pretype,
                    syntab['type'][jj])
                if len(gk) == 0:
                    continue
                plt.plot(self.tseries,
                         gk - shift,
                         color=l2d[0].get_color(),
                         ls=lstyles[syntab['type'][jj]],
                         label='%s:%s<-%s' % (syntab['type'][jj], 
                                              syntab['dest'][jj].split('/')[0], 
                                              pretype))
            shift += 1

        return precells_with_vm

    def plot_traces(self, cellname, targettime, historytime, srctype, syntype):
        """Plot traces of presynaptic data for cellname for `historytime`
        around `targettime`."""
        self.tstart = targettime - historytime
        self.istart = int(self.tstart / self.plotdt + 0.5)
        self.tend = targettime + historytime
        self.iend = int(self.tend / self.plotdt + 0.5)
        self.tseries = np.linspace(self.tstart, self.tend, 
                                 self.iend - self.istart)
        if cellname not in self.datafile['/Vm']:
            return []
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
        try:
            data = self.datafile['/Vm/'+cellname][istart:iend]
        except KeyError:
            print 'get_peak_Vm_time: no Vm entry for', cellname
            return -1
        peakindex = data.argmax()
        peaktime = tstart + peakindex * self.plotdt
        print 'peak time:', cellname, ':', peaktime
        return peaktime

    def loop_plot_presyn(self, targetcells, targettime, contexttime, pretype, syntype):
        precells = [targetcells]
        done_cells = set()
        timequeue = [[targettime] * len(targetcells)]
        # mgr = plt.get_current_fig_manager()
        # if mgr.__class__.__name__.endswith('GTKAgg'):
        #     mgr.full_screen_toggle()
        while precells:        
            newtimes = []
            for precell, targettime in zip(precells.pop(0), timequeue.pop(0)):
                if precell in done_cells or targettime < 0:
                    continue
                pre = synan.plot_traces(precell,
                                        targettime,
                                        contexttime,
                                        pretype,
                                        syntype)
                precells.append(pre)
                done_cells.add(precell)
                new_targettime = self.get_peak_Vm_time(precell, 
                                                       targettime-contexttime, 
                                                       targettime+contexttime)                
                newtimes.append(new_targettime)
                plt.legend()
                plt.setp(plt.gca().get_legend().get_texts(), fontsize='small')
                # mgr = plt.get_current_fig_manager()
                # if mgr.__class__.__name__.endswith('GTKAgg'):
                #     mgr.full_screen_toggle()
                plt.show()
            if newtimes:
                timequeue.append(newtimes)
        
        
if __name__ == '__main__':
    dfname = '/data/subha/cortical/py/data/2012_04_26/data_20120426_142251_7866.h5'
    synan = SynAnalyzer(dfname)
    targettime = 7.0
    contexttime = 0.05
    targetcell = 'SpinyStellate_1'
    presyn = '' # All pre synaptic celltypes
    syntype = '' # All synapse types
    synan.loop_plot_presyn([targetcell], targettime, contexttime, presyn, syntype)
    # precells = []
    # done_cells = set(['SpinyStellate_0'])
    # plt.clf()
    # pre = synan.plot_traces(['SpinyStellate_1'], 
    #                         targettime,
    #                         contexttime,
    #                         '',
    #                         '')
    # precells.append(pre)
    # plt.legend()
    # plt.setp(plt.gca().get_legend().get_texts(), fontsize='small')
    # mgr = plt.get_current_fig_manager()
    # # if mgr.__class__.__name__.endswith('GTKAgg'):
    # #     mgr.full_screen_toggle()
    # plt.show()
    # while precells:        
    #     old_targettime = targettime
    #     for precell in precells.pop(0):
    #         if precell in done_cells:
    #             continue
    #         done_cells.add(precell)
    #         targettime = synan.get_peak_Vm_time(precell, 
    #                                             old_targettime-contexttime, 
    #                                             old_targettime+contexttime)
    #         pre = synan.plot_traces(precell,
    #                                 targettime,
    #                                 contexttime,
    #                                 '',
    #                                 '')
    #         precells.append(pre)
    #         plt.legend()
    #         plt.setp(plt.gca().get_legend().get_texts(), fontsize='small')
    #         mgr = plt.get_current_fig_manager()
    #         # if mgr.__class__.__name__.endswith('GTKAgg'):
    #         #     mgr.full_screen_toggle()
    #         plt.show()
    #     old_targettime -= contexttime
    #     if old_targettime < 0:
    #         break

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
