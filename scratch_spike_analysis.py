# scratch_spike_analysis.py --- 
# 
# Filename: scratch_spike_analysis.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Dec 12 11:43:23 2012 (+0530)
# Version: 
# Last-Updated: Tue Dec 18 20:22:19 2012 (+0530)
#           By: subha
#     Update #: 264
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

# Code:

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import ColorConverter
import igraph as ig
from traubdata import TraubData
import peakdetect as pdet
import analyzer
from savitzkygolay import savgol
import util        
import networkx as nx

if __name__ == '__main__':
    data = TraubData('/data/subha/rsync_ghevar_cortical_data_clone/2012_11_07/data_20121107_100729_29479.h5')
    cats = data.get_pop_ibi('SpinyStellate')
    synapses = data.fnet['/network/synapse']
    pre_cells = np.char.split(synapses['source'], '/')
    pre_cells = [row[0] for row in pre_cells]
    post_cells = np.char.split(synapses['dest'], '/')
    post_cells = [row[0] for row in post_cells]
    gk = []    
    cells = sorted(set(pre_cells).union(set(post_cells)))
    cell_index_map = dict([(cell, index) for index, cell in enumerate(cells)])
    print cell_index_map
    g = ig.Graph(0)
    print g
    g.add_vertices(len(cells))
    print g
    cellcount = sum(data.fnet['/network/celltype']['count'])
    edges = [(cell_index_map[pre], cell_index_map[post]) for pre, post in zip(pre_cells, post_cells)]
    g.add_edges(edges)
    assert(len(g.vs) == cellcount)
    colordict = util.load_celltype_colors()
    celltype = [cellname.split('_')[0] for cellname in cells]
    g.vs['celltype'] = celltype
    g.vs['color'] = [colordict[celltype] for celltype in g.vs['celltype']]
    # ig.plot(g)
    g1 = nx.MultiDiGraph()
    edges = [(row['source'], row['dest'], {'weight': float(row['Gbar'])}) for row in synapses]
    g1.add_edges_from(edges)
    node_colors = []
    for node in g1.nodes():
        if node in cats['odd_cells']:
            node_colors.append('cyan')
        else:
            node_colors.append(colordict[node.split('_')[0]])
    color_conv = ColorConverter()
    for index, node in enumerate(g1.nodes()):
        r, g, b = color_conv.to_rgb(node_colors[index])
        g1.node[node]['r'] = int(r*255)
        g1.node[node]['g'] = int(g*255)
        g1.node[node]['b'] = int(b*255)
                
        print g1.node[node]
    nx.write_pajek(g1, 'cellgraph.net')
    nx.write_graphml(g1, 'cellnet.graphml')
    # nx.draw_graphviz(g1, node_color=node_colors, alpha=0.5, edge_color=[(0.5,0.5,0.5, 0.2)] * len(g1.edges()), with_labels=False)
    # plt.show()
    # combined_spikes = []
    # for cell, spiketimes in data.spikes.items():
    #     if cell.startswith('Spiny'):
    #         # np.savetxt('testspiketrain.txt', spiketimes)
    #         start, length, RS = ranksurprise.burst(spiketimes, 20e-3, 5.0)
    #         end = start+length-1
    #         plt.plot(spiketimes, np.ones(len(spiketimes)), 'rx')
    #         plt.plot(spiketimes[start], np.ones(len(start)), 'bv')
    #         plt.plot(spiketimes[end], np.ones(len(end)), 'g^')
    #         plt.show()
    #         plt.close()


# 
# scratch_spike_analysis.py ends here
