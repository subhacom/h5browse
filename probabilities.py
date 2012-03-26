# probabilities.py --- 
# 
# Filename: probabilities.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Mon Mar 19 23:25:51 2012 (+0530)
# Version: 
# Last-Updated: Mon Mar 26 17:10:16 2012 (+0530)
#           By: subha
#     Update #: 626
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

# Code:

import numpy as np
import h5py as h5
import igraph as ig
from datetime import datetime

excitatory_celltypes = [
    'SupPyrRS',
    'SupPyrFRB',
    'SpinyStellate',
    'TuftedIB',
    'TuftedRS',
    'NontuftedRS',
    'TCR'
    ]

class SpikeCondProb(object):
    def __init__(self, datafilepath, netfilepath, netfilepath_new=None):
        self.datafile = h5.File(datafilepath, 'r')
        self.netfile = h5.File(netfilepath, 'r')
        if netfilepath_new:
            self.netfile_new = h5.File(netfilepath_new, 'r')

        self.schedinfo = {}
        for row in self.datafile['/runconfig/scheduling']:
            try:
                value = float(row[1])
                self.schedinfo[row[0]] = value
            except ValueError:
                pass

        self.__load_ampa_graph()
        self.__load_spiketrains()
        self.__load_stimuli()
        
    def __del__(self):
        if hasattr(self, 'datafile'):
            self.datafile.close()
        if hasattr(self, 'netfile'):
            self.netfile.close()
        if hasattr(self, 'netfile_new'):
            self.netfile_new.close()
            
    def __load_ampa_graph(self):
        celltype_counts = np.sort(np.asarray(self.netfile['/network/celltype']), order='index')
        cellcount = np.sum(celltype_counts['count'])
        print 'Total cell count', cellcount
        start_index = 0
        cell_start = {}
        self.cells = []
        celltype_list = []
        for (celltype, count) in zip(celltype_counts['name'], celltype_counts['count']):
            cell_start[celltype] = start_index
            self.cells.extend(['%s_%d' % (celltype, ii) for ii in range(count)])
            celltype_list.extend([celltype] * count)
            start_index += count
        assert(len(self.cells) == start_index)
        graph = ig.Graph(0, directed=True)
        graph.add_vertices(start_index)
        graph.vs['name'] = self.cells
        graph.vs['type'] = celltype_list
        ampa_syn = np.asarray(self.netfile['/network/cellnetwork/gampa'])
        sources =  np.array(ampa_syn[:,0], dtype=int)
        targets = np.array(ampa_syn[:,1], dtype=int)
        print 'Number of AMPA synapse:', sources.shape
        edges = zip(sources.tolist(), targets.tolist())
        graph.add_edges(edges)
        self.ampa_graph = graph

    def __load_spiketrains(self):
        self.spikes = {}
        for cellname in self.datafile['/spikes']:
            self.spikes[cellname] = np.asarray(self.datafile['/spikes'][cellname])

    def __load_stimuli(self):
        self.bg_stim = self.datafile['stimulus/stim_bg'][:]
        self.probe_stim = self.datafile['stimulus/stim_probe'][:]
        self.bg_times = (np.nonzero(np.diff(self.bg_stim) < 0)[0] + 1.0) * self.schedinfo['simdt'] # extract the indices where bg stim went from hi->lo
        self.probe_times = (np.nonzero(np.diff(self.probe_stim) < 0)[0] + 1.0) * self.schedinfo['simdt']

    def calc_spike_prob(self, precell, postcell, window_width, delay=0.0):
        """Calculate the fraction of spikes in precell for which
        postcell fires at least once within (delay,
        delay+window_width] interval."""
        count = 0
        for prespike in self.spikes[precell]:
            indices = np.nonzero((self.spikes[postcell] > prespike + delay) & (self.spikes[postcell] <= prespike + delay + window_width))[0]
            if len(indices) > 0:
                count += 1
        return count * 1.0 / len(self.spikes[precell])

    def calc_spike_prob_all_connected(self, width, delay=0.0):
        """Calculate, for each pair of connected cells, the fraction
        of times the post synaptic cell fires within an interval
        (delay, width+delay] period"""        
        spike_prob_connected = {}
        for edge in self.ampa_graph.es:
            precell = self.ampa_graph.vs[edge.source]['name']
            postcell = self.ampa_graph.vs[edge.target]['name']
            spike_prob_connected['%s-%s' % (precell, postcell)] = self.calc_spike_prob(precell, postcell, width, delay)
        return spike_prob_connected

    def calc_spike_prob_all_unconnected(self, width, delay=0.0):
        """Calculate the spikeing probability of, for each source, an
        unconnected taget."""
        spike_prob_unconnected = {}
        for edge in self.ampa_graph.es:
            pre_vertex = self.ampa_graph.vs[edge.source]
            forbidden = set([edge.source])
            for nn in self.ampa_graph.neighbors(edge.source, ig.OUT):
                forbidden.add(nn)
            post_type = self.ampa_graph.vs[edge.target]['type']
            post_vs = self.ampa_graph.vs.select(type_eq=post_type)
            indices = range(len(post_vs))
            index = np.random.randint(len(post_vs))
            while post_vs[index].index in forbidden or '%s-%s' % (pre_vertex['name'], post_vs[index]['name']) in spike_prob_unconnected:
                index = np.random.randint(len(post_vs))
            precell = pre_vertex['name']
            postcell = post_vs[index]['name']
            print 'Selected unconnected cell pair:', precell, postcell
            spike_prob_unconnected['%s-%s' % (precell, postcell)] = self.calc_spike_prob(precell, postcell, width, delay)
        return spike_prob_unconnected

    def get_excitatory_subgraph(self):
        if not hasattr(self, 'excitatory_subgraph'):
            self.excitatory_subgraph = self.ampa_graph.subgraph(self.ampa_graph.vs.select(lambda v: v['type'] in excitatory_celltypes))
        return self.excitatory_subgraph
        
    def calc_spike_prob_excitatory_connected(self, width, delay=0.0):
        spike_prob = {}
        for edge in self.get_excitatory_subgraph().es:
            precell = self.get_excitatory_subgraph().vs[edge.source]['name']
            postcell = self.get_excitatory_subgraph().vs[edge.target]['name']
            spike_prob['%s-%s' % (precell, postcell)] = self.calc_spike_prob(precell, postcell, width, delay)
            # print '$', precell, postcell
        return spike_prob

    def calc_spike_prob_excitatory_unconnected(self, width, delay):
        spike_prob = {}
        for edge in self.get_excitatory_subgraph().es:
            pre = self.get_excitatory_subgraph().vs[edge.source]
            post = self.get_excitatory_subgraph().vs[edge.target]
            forbidden = set(self.get_excitatory_subgraph().neighbors(edge.source, ig.OUT))
            post_vs = self.get_excitatory_subgraph().vs.select(type_eq=post['type'])
            indices = range(len(post_vs))
            index = np.random.randint(len(post_vs))
            while post_vs[index].index in forbidden or '%s-%s' % (pre['name'], post_vs[index]['name']) in spike_prob:
                index = np.random.randint(len(post_vs))
            precell = pre['name']
            postcell = post_vs[index]['name']
            spike_prob['%s-%s' % (precell, postcell)] = self.calc_spike_prob(precell, postcell, width, delay)
            # print '#', precell, post['name'], postcell
        return spike_prob

    def calc_prespike_prob_excitatory_connected(self, width, delay):
        """Calculate the probability of a presyanptic spike for each
        post synaptic cell.  This is done by computing the fraction of
        spikes in the presynaptic cell that fall within a window of
        width {width} at {delay} time ahead of the post synaptic
        spike.
        """
        spike_prob = {}
        for edge in self.get_excitatory_subgraph().es:
            precell = self.get_excitatory_subgraph().vs[edge.source]['name']
            postcell = self.get_excitatory_subgraph().vs[edge.target]['name']
            spike_prob['%s-%s' % (precell, postcell)] = self.calc_spike_prob(postcell, precell, width, -delay)
        return spike_prob
            
    def calc_prespike_prob_excitatory_unconnected(self, width, delay):
        """Calculate the probability of a random unconnected cell
        spiking within a window of width {width} {delay} period before
        spiking in a cell."""
        spike_prob = {}
        for edge in self.get_excitatory_subgraph().es:
            pre = self.get_excitatory_subgraph().vs[edge.source]
            post = self.get_excitatory_subgraph().vs[edge.target]
            forbidden = set(self.get_excitatory_subgraph().neighbors(edge.target, ig.IN))
            pre_vs = self.get_excitatory_subgraph().vs.select(type_eq=pre['type'])
            indices = range(len(pre_vs))
            index = np.random.randint(len(pre_vs))
            while pre_vs[index].index in forbidden or '%s-%s' % (pre_vs[index]['name'], post['name']) in spike_prob:
                index = np.random.randint(len(pre_vs))
            precell = pre_vs[index]['name']
            postcell = post['name']
            spike_prob['%s-%s' % (precell, postcell)] = self.calc_spike_prob(postcell, precell, width, -delay)
        return spike_prob

    def calc_spike_prob_after_bgstim(self, cell, width, delay):
        """Calculate the probability of spike following a background
        stimulus"""
        bg_spike_prob = 0
        only_bg_count = len(self.bg_times) - len(self.probe_times)
        if only_bg_count <= 0:
            return 0.0
        # print 'bg_times', self.bg_times
        ii = 0
        while ii  < len(self.bg_times):
            win_start = self.bg_times[ii] + delay
            win_end = win_start + width
            # print win_start, win_end
            spike_count = np.nonzero((self.spikes[cell] > win_start) & 
                                     (self.spikes[cell] <= win_end))[0]
            # print spike_count
            if spike_count > 0:
                bg_spike_prob += 1.0
            ii += 2
        return bg_spike_prob / only_bg_count

    def calc_spikecount_avg_after_bgstim(self, cell, width, delay):
        """Calculate the probability of spike following a background
        stimulus"""
        spike_count = 0.0
        only_bg_count = len(self.bg_times) - len(self.probe_times)
        # print 'only_bg_count:', only_bg_count
        if only_bg_count <= 0:
            return 0.0
        ii = 0
        while ii < len(self.bg_times):
            win_start = self.bg_times[ii] + delay
            win_end = win_start + width
            # print win_start, win_end
            spike_count += len(np.nonzero((self.spikes[cell] > win_start) & 
                                      (self.spikes[cell] <= win_end))[0])
            ii += 2
        return spike_count / only_bg_count

    def calc_spike_prob_after_probestim(self, cell, width, delay):
        """Calculate the probability of spike following a background
        stimulus"""
        probe_spike_prob = 0
        # print 'probe_times:', self.probe_times
        for ii in range(len(self.probe_times)):
            win_start = self.probe_times[ii] + delay
            win_end = win_start + width
            # print win_start, win_end
            spike_count = np.nonzero((self.spikes[cell] > win_start) & 
                                      (self.spikes[cell] <= win_end))[0]
            if spike_count > 0:
                probe_spike_prob += 1.0
        return probe_spike_prob / len(self.probe_times)

    def calc_spikecount_avg_after_probestim(self, cell, width, delay):
        """Calculate the probability of spike following a background
        stimulus"""
        spike_count = 0.0
        for ii in range(len(self.probe_times)):
            spike_count += len(np.nonzero((self.spikes[cell] > (self.probe_times[ii] + delay)) & 
                                      (self.spikes[cell] <= (self.probe_times[ii] + delay + width)))[0])
        return spike_count / len(self.probe_times)
        

import pylab    
def test_main():
    datafilepath = 'test_data/data.h5'
    netfilepath = 'test_data/network.h5'
    window = 10e-3
    delay = 10e-3
    cond_prob = SpikeCondProb(datafilepath, netfilepath)
    spike_prob = cond_prob.calc_spike_prob_all_connected(window, delay)
    print 'TCR_0->SupPyrRS_1: spike following probability', spike_prob
    pylab.subplot(2,1,1)
    pylab.hist(spike_prob.values(), normed=True)
    pylab.subplot(2,1,2)
    spike_unconn_prob_0 = cond_prob.calc_spike_prob('TCR_0', 'SupPyrRS_0', window, delay)
    print 'TCR_0->SupPyrRS_0: probability of spike following', spike_unconn_prob_0
    spike_unconn_prob = cond_prob.calc_spike_prob_all_unconnected(30e-3)
    print spike_unconn_prob
    pylab.hist(spike_unconn_prob.values(), normed=True)
    pylab.show()

from matplotlib import pyplot    
from matplotlib.backends.backend_pdf import PdfPages
params = {'font.size' : 10,
          'axes.labelsize' : 10,
          'font.size' : 10,
          'text.fontsize' : 10,
          'legend.fontsize': 10,
          'xtick.labelsize' : 8,
          'ytick.labelsize' : 8}

def run_on_files(filelist, windowlist, delaylist, mode):
    """Go through specified datafiles and dump the probability
    historgrams.

    For each entry in window list it goes through all delay values in
    delaylist.

    Mode decides what to calculate: 

    mode='pre' calculates the probability of a spike preceding a post
    synaptic spike by delay interval within a window of width
    specified in windowlist. Same calculation is done for a randomly
    chosen non adjacent cell. The data is dumped in files named
    'exc_pre_hist_{ID}.pdf' as plot and 'exc_pre_prob_{ID}.h5' as
    table.

    mode='post' calculates the probability of a spike following a
    presynaptic spike by delay interval within a window of width
    specified in windowlist. Same calculation is done for a randomly
    chosen unconnected cells. The data is dumped in files named
    'exc_hist_{ID}.pdf' as plot and 'exc_prob_{ID}.h5' as table.
    """
    pyplot.rcParams.update(params)
    unconn_fun = SpikeCondProb.calc_spike_prob_excitatory_unconnected
    conn_fun = SpikeCondProb.calc_spike_prob_excitatory_connected
    file_prefix = 'exc'
    if mode == 'pre':
        unconn_fun = SpikeCondProb.calc_prespike_prob_excitatory_unconnected
        conn_fun = SpikeCondProb.calc_prespike_prob_excitatory_connected
        file_prefix = 'exc_pre'
    
    for datafilepath in filelist:
        start = datetime.now()
        netfilepath = datafilepath.replace('/data_', '/network_')
        print 'Netfile path', netfilepath
        outfilepath = datafilepath.replace('/data_', '/%s_hist_' % (file_prefix)).replace('.h5', '.pdf')
        dataoutpath = datafilepath.replace('/data_', '/%s_prob_' % (file_prefix))
        dataout = h5.File(dataoutpath, 'w')
        grp = dataout.create_group('/spiking_prob')
        outfile = PdfPages(outfilepath)
        prob_counter = SpikeCondProb(datafilepath, netfilepath)
        jj = 0
        for window in windowlist:
            rows = len(delaylist)
            cols = 2
            if rows * cols < len(delaylist):
                rows += 1
            figure = pyplot.figure()
            ii = 0
            for delay in delaylist:
                connected_prob = conn_fun(prob_counter, window, delay)
                dset = grp.create_dataset('conn_window_%d_delta_%d' % (jj, ii/2), data=np.asarray(connected_prob.items(), dtype=('|S35,f')))
                dset.attrs['delay'] = delay
                dset.attrs['window'] = window
                unconnected_prob = unconn_fun(prob_counter, window, delay)
                dset = grp.create_dataset('unconn_window_%d_delta_%d' % (jj, ii/2), data=np.asarray(unconnected_prob.items(), dtype=('|S35,f')))            
                dset.attrs['delay'] = delay
                dset.attrs['window'] = window
                data = [np.asarray(connected_prob.values()), np.asarray(unconnected_prob.values())]
                labels = ['conn w:%g,d:%g' % (window, delay), 'unconn w:%g,d:%g' % (window, delay)]
                axes = pyplot.subplot(rows, cols, ii+1)
                pyplot.hist(data, bins=np.arange(0, 1.1, 0.1), normed=True, histtype='bar', label=labels)
                pyplot.legend(prop={'size':'xx-small'})
                pyplot.ylim([0, 10.0])
                pyplot.xlim([0, 1.1])
                axes = pyplot.subplot(rows, cols, ii+2)
                pyplot.hist(data, bins=np.arange(0, 1.1, 0.1), normed=True, histtype='step', cumulative=True, label=labels)
                pyplot.legend(prop={'size':'xx-small'})
                pyplot.ylim([0, 10.0])
                pyplot.xlim([0, 1.1])
                ii += 2
                print 'finished delay:', delay
            jj += 1
            print 'finished window', window
            outfile.savefig(figure)
            figure.clf()
        dataout.close()
        outfile.close()
        end = datetime.now()
        delta = end - start        
        print 'Finished:', netfilepath, 'in', (delta.seconds + 1e-6 * delta.microseconds)
                

import sys
    
if __name__ == '__main__':
    # test_main()
    if len(sys.argv) < 3:
        print 'Usage:', sys.argv[0], 'filelist mode'
        print 'where file list is a text file with one data file path in each line. mode can be \'pre\' or \'post\'. Dumps pre/post synaptic spike probabilities from spike train data.'
        sys.exit(0)
    files = [line.strip().replace('.new', '') for line in open(sys.argv[1], 'r')]
    if sys.argv[2] == 'pre':
        delays = np.arange(11e-3, 51e-3, 10e-3)
    else:
        delays = np.arange(1e-3, 41e-3, 10e-3)

    run_on_files(files, [10e-3], delays, sys.argv[2])
    
# 
# probabilities.py ends here
