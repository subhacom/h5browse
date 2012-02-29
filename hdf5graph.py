# hdf5graph.py --- 
# 
# Filename: hdf5graph.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Feb 29 16:25:03 2012 (+0530)
# Version: 
# Last-Updated: Wed Feb 29 18:54:18 2012 (+0530)
#           By: subha
#     Update #: 112
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# HDF5 network file is converted into an igraph graph (and may be
# saved in standard graph format).
# 
# 

# Change log:
# 
# 
# 
# 

# Code:

import igraph as ig
import h5py as h5
import numpy

class HDFGraph(object):
    def __init__(self, filename):
        fileh = h5.File(filename, 'r')
        self.sources = []
        self.dests = []
        self.weights = []
        self.nodes = set()
        self.name_node = {}
        self.node_name = {}
        synrows = numpy.asarray(fileh['/network/synapse'])
        src_index_dict = {}
        dest_index_dict = {}
        for ii in range(len(synrows)):
            row = synrows[ii]
            source = row[0].partition('/')[0]
            dest = row[1].partition('/')[0]
            weight = float(row[3])
            src_index_dict[source] = ii
            dest_index_dict[dest] = ii
            self.sources.append(source)
            self.dests.append(dest)
            self.weights.append(weight)
        
        
        #     self.sources.append()
        #     self.dests.append()
        #     self.weights.append()
        src_set = set(self.sources)
        dest_set = set(self.dests)
        node_set = src_set | dest_set
        index = 0
        for nname in node_set:
            self.name_node[nname] = index
            self.node_name[index] = nname
            index += 1
        self.graph = ig.Graph(0,directed=True)
        self.graph.add_vertices(len(node_set))
        edges = [(self.name_node[self.sources[ii]], self.name_node[self.dests[ii]]) for ii in range(len(self.sources))]
        self.graph.add_edges(edges)
        self.graph.vs['label'] = [self.node_name[node] for node in range(len(self.node_name))]
        self.graph.es['weight'] = self.weights
        # for ii in range(len(self.weights)):
        #     src_index = self.name_node[self.sources[ii]]
        #     dest_index = self.name_node[self.dest[ii]]
        #     self.graph.es
        
        # self.graph.es['weight'] = [
        # # for ii in range(len(self.sources)):
        # #     self.graph.es[ii]['weight'] = self.weights[ii]
        # for node, name in self.node_name.items():
        #     self.graph.vs[node]['label'] = name
        
        
if __name__ == '__main__':
    g = HDFGraph('../py/data/2012_02_01/network_20120201_204744_29839.h5.new')
    ig.plot(g.graph)

# 
# hdf5graph.py ends here
