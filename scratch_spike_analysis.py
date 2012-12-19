# scratch_spike_analysis.py --- 
# 
# Filename: scratch_spike_analysis.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Dec 12 11:43:23 2012 (+0530)
# Version: 
# Last-Updated: Wed Dec 19 21:17:36 2012 (+0530)
#           By: subha
#     Update #: 349
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
from collections import defaultdict
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
    colordict = util.load_celltype_colors()
    data = TraubData('/data/subha/rsync_ghevar_cortical_data_clone/2012_11_07/data_20121107_100729_29479.h5')
    cats = data.get_pop_ibi('SpinyStellate')
    graph = data.get_cell_graph()
    spinstell_count = dict(zip(data.fnet['/network/celltype']['name'], data.fnet['/network/celltype']['count']))['SpinyStellate']
    print spinstell_count
    g1 = nx.DiGraph()
    for e in graph.edges(data=True):
        print e
        if g1.has_edge(e[0], e[1]):
            g1[e[0]][e[1]]['weight'] += e[2]['weight']
        else:
            g1.add_edge(*e)
    hubs, authorities = nx.hits(g1)
    g2 = g1.subgraph(['SpinyStellate_%d' % (idx) for idx in range(spinstell_count)])
    node_colors = []
    for node in g2.nodes():
        if node in cats['odd_cells']:
            node_colors.append('cyan')
        else:
            node_colors.append(colordict[node.split('_')[0]])
    layout = nx.spring_layout(g2)
    nodes =nx.draw_networkx_nodes(g2, pos=layout, node_color=node_colors)
    labels = nx.draw_networkx_labels(g2, pos=layout, labels=dict([(cell, hubs[cell]) for cell in g2.nodes()]))
    plt.show()
    # nx.draw_graphviz(graph, node_color=[graph.node[cell]['color'] for cell in graph.nodes()])
    # plt.show()


    # synapses = data.fnet['/network/synapse']
    # pre_cells = [row[0] for row in np.char.split(synapses['source'], '/')]
    # post_cells = [row[0] for row in np.char.split(synapses['dest'], '/')]
    # weights = [g for g in synapses['Gbar']]
    # cells = sorted(set(pre_cells).union(set(post_cells)))
    # cell_index_map = dict([(cell, index) for index, cell in enumerate(cells)])
    # # print cell_index_map
    # cellcount = sum(data.fnet['/network/celltype']['count'])    
    # edges = defaultdict(float)
    # for ii in range(len(weights)):
    #     edges[(pre_cells[ii], post_cells[ii])] += float(weights[ii])
    # print len(edges)
    # # g = ig.Graph(n=len(cells), 
    # #              edges=edges.keys(),
    # #              directed=True)
    # # g.es['weight'] = [edges[e] for e in g.es]
    # # assert(len(g.vs) == cellcount)
    # # celltype = [cellname.split('_')[0] for cellname in cells]
    # # g.vs['celltype'] = celltype
    # # g.vs['color'] = [colordict[celltype] for celltype in g.vs['celltype']]
    # # ig.plot(g)
    # g1 = nx.MultiDiGraph()
    # g1.add_edges_from([(e[0], e[1], {'weight': value}) for e, value in edges.items()])
    # node_colors = []
    # for node in g1.nodes():
    #     if node in cats['odd_cells']:
    #         node_colors.append('cyan')
    #     else:
    #         node_colors.append(colordict[node.split('_')[0]])
    # g2 = 
    # color_conv = ColorConverter()
    # for index, node in enumerate(g1.nodes()):
    #     r, g, b = color_conv.to_rgb(node_colors[index])
    #     g1.node[node]['r'] = int(r*255)
    #     g1.node[node]['g'] = int(g*255)
    #     g1.node[node]['b'] = int(b*255)
                
    #     print g1.node[node]
    # nx.write_pajek(g1, 'cellgraph.net')
    # nx.write_graphml(g1, 'cellnet.graphml')
    # nx.draw_graphviz(g1, node_color=node_colors, alpha=0.5, edge_color=[(0.5,0.5,0.5, 0.2)] * len(g1.edges()), with_labels=False)
    # plt.show()
    # # combined_spikes = []
    # # for cell, spiketimes in data.spikes.items():
    # #     if cell.startswith('Spiny'):
    # #         # np.savetxt('testspiketrain.txt', spiketimes)
    # #         start, length, RS = ranksurprise.burst(spiketimes, 20e-3, 5.0)
    # #         end = start+length-1
    # #         plt.plot(spiketimes, np.ones(len(spiketimes)), 'rx')
    # #         plt.plot(spiketimes[start], np.ones(len(start)), 'bv')
    # #         plt.plot(spiketimes[end], np.ones(len(end)), 'g^')
    # #         plt.show()
    # #         plt.close()


# 
# scratch_spike_analysis.py ends here
