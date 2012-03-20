# probabilities.py --- 
# 
# Filename: probabilities.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Mon Mar 19 23:25:51 2012 (+0530)
# Version: 
# Last-Updated: Tue Mar 20 16:58:45 2012 (+0530)
#           By: subha
#     Update #: 179
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

class SpikeCondProb(object):
    def __init__(self, datafilepath, netfilepath, netfilepath_new=None):
        self.datafile = h5.File(datafilepath, 'r')
        self.netfile = h5.File(netfilepath, 'r')
        if netfilepath_new:
            self.netfile_new = h5.File(netfilepath_new, 'r')

        self.__load_ampa_graph()
        self.__load_spiketrains()
        
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
        print len(self.cells), start_index
        graph = ig.Graph(0, directed=True)
        graph.add_vertices(start_index)
        graph.vs['name'] = self.cells
        graph.vs['type'] = celltype_list
        ampa_syn = np.asarray(self.netfile['/network/cellnetwork/gampa'])
        sources =  np.array(ampa_syn[:,0], dtype=int)
        targets = np.array(ampa_syn[:,1], dtype=int)
        print sources.shape, targets.shape
        edges = zip(sources.tolist(), targets.tolist())
        graph.add_edges(edges)
        self.ampa_graph = graph

    def __load_spiketrains(self):
        self.spikes = {}
        for cellname in self.datafile['/spikes']:
            self.spikes[cellname] = np.asarray(self.datafile['/spikes'][cellname])

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
            while post_vs[index].index in forbidden:
                index = np.random.randint(len(post_vs))
            precell = pre_vertex['name']
            postcell = post_vs[index]['name']
            spike_prob_unconnected['%s-%s' % (precell, postcell)] = self.calc_spike_prob(precell, postcell, width, delay)
        return spike_prob_unconnected

import pylab    
def test_main():
    datafilepath = 'test_data/data.h5'
    netfilepath = 'test_data/network.h5'
    window = 10e-3
    delay = 10e-3
    cond_prob = SpikeCondProb(datafilepath, netfilepath)
    spike_prob = cond_prob.calc_spike_prob_all_connected(window, delay)
    print 'TCR_2->SupPyrRS_4: spike following probability', spike_prob
    pylab.subplot(2,1,1)
    pylab.hist(spike_prob.values(), normed=True)
    pylab.subplot(2,1,2)
    spike_unconn_prob_0 = cond_prob.calc_spike_prob('TCR_2', 'SupPyrRS_0', window, delay)
    print 'TCR_2->SupPyrRS_0: probability of spike following', spike_unconn_prob_0
    spike_unconn_prob = cond_prob.calc_spike_prob_all_unconnected(30e-3)
    print spike_unconn_prob
    pylab.hist(spike_unconn_prob.values(), normed=True)
    pylab.show()
    
    
if __name__ == '__main__':
    test_main()
    
# 
# probabilities.py ends here
