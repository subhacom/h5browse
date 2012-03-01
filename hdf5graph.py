# hdf5graph.py --- 
# 
# Filename: hdf5graph.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Feb 29 16:25:03 2012 (+0530)
# Version: 
# Last-Updated: Thu Mar  1 19:54:52 2012 (+0530)
#           By: subha
#     Update #: 195
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
import sys
import igraph as ig
import h5py as h5
import numpy

class HDFGraph(object):
    def __init__(self, filename):
        self.filename = filename
        filehandle = h5.File(filename, 'r')
        self.syntab = numpy.asarray(filehandle['/network/synapse'])
        self.graph = ig.Graph(0, directed=True)
        src = [row[0].rpartition('/')[0] for row in self.syntab]
        dst = [row[1].rpartition('/')[0] for row in self.syntab]
        weight = [row[3] for row in self.syntab]
        nodeset = set(src) | set(dst)
        nodeindex = dict(zip(nodeset, range(len(nodeset))))
        self.graph.add_vertices(len(nodeset))
        self.graph.add_edges([(nodeindex[src[ii]], 
                               nodeindex[dst[ii]]) 
                              for ii in range(len(src))])
        self.graph.es['weight'] = weight
        self.graph.vs['label'] = list(nodeset)

    def write_dot(self, filename):
        self.graph.write_dot(filename)

    def write_gml(self, filename):
        self.graph.write_gml(filename)

    def get_vclustering(self, membership=None, modularity=None):
        return ig.VertexClustering(self.graph, 
                                   membership=membership, 
                                   modularity=modularity)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "../py/data/2012_02_08/network_20120208_115556_4589.h5.new"
    g = HDFGraph(filename)
    dot_file = g.filename.replace('.h5', '').replace('new', 'dot')
    gml_file = g.filename.replace('.h5', '').replace('new', 'gml')
    g.write_gml(gml_file)
    g.write_dot(dot_file) 
    clusters = g.graph.clusters()
    print clusters.size_histogram()
    for cluster in clusters:
        print cluster
    # membership = g.clusters()
    # clustering = g.get_vclustering(membership=g.graph.clusters().membership)
    # for ii in range(len(clustering)):
    #     cluster = clustering.subgraph(ii)
    #     print len(cluster)
    #     # ig.plot(cluster)

# 
# hdf5graph.py ends here
