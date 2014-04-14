# scratch_spike_analysis.py --- 
# 
# Filename: scratch_spike_analysis.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Dec 12 11:43:23 2012 (+0530)
# Version: 
# Last-Updated: Mon Dec 24 21:24:34 2012 (+0530)
#           By: subha
#     Update #: 762
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

import random
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

def draw_spinstell_hits_graph(data, burst_cats):
    """Draw spiny stellate cells with labels as HITS authority/hub
    value.  'odd_cells' in burst_cats dict are displayed in cyan,
    others in purple.
    """
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
        if node in burst_cats['odd_cells']:
            node_colors.append('cyan')
        else:
            node_colors.append(colordict[node.split('_')[0]])
    layout = nx.spring_layout(g2)
    nodes =nx.draw_networkx_nodes(g2, pos=layout, node_color=node_colors)
    labels = nx.draw_networkx_labels(g2, pos=layout, labels=dict([(cell, hubs[cell]) for cell in g2.nodes()]))
    plt.show()

def plot_with_marker(data, cells, marker, startindex=0, timerange=(0, 1e9)):
    for cell in cells:
        spikes = data.spikes[cell]
        spikes = spikes[(spikes >= timerange[0]) & (spikes < timerange[1])].copy()
        plt.plot(spikes, np.ones(len(spikes)) * startindex, marker)
        startindex += 1
    return startindex
    
def plot_burst_intervals(data, timerange=(0, 1e9)):
    cats = data.get_pop_ibi('SpinyStellate', timerange=timerange)
    cells = [ss for ss in data.spikes.keys() if ss.startswith('Spiny')]
    odd_cells = set(cats['odd_cells'])
    good_cells = set(cells) - odd_cells
    index = 1
    index = plot_with_marker(data, good_cells, 'b+', index, timerange)
    index = plot_with_marker(data, odd_cells, 'c+', index, timerange)
    ibi_start, ibi_end, = cats['pop_ibi']
    print ibi_end
    plt.bar(ibi_start, 
            height=np.ones(len(ibi_start))*index,
            width=np.array(np.array(ibi_end) - np.array(ibi_start)),
            alpha=0.2)

def plot_odd_cells_net(data):
    cats = data.get_pop_ibi('SpinyStellate')
    odd_cells = set(cats['odd_cells'])
    cells = set([ss for ss in data.spikes.keys() if ss.startswith('SpinyStellate')])
    good_cells = cells - odd_cells
    good_cells = random.sample(good_cells, len(odd_cells))
    net = data.get_cell_graph()
    cmap = plt.cm.PuOr
    emax = max(data.fnet['/network/synapse']['Gbar'])
    for good, bad in zip(good_cells, odd_cells):        
        goodsub = net.subgraph([good] + net.predecessors(good)).copy()
        for b in odd_cells:
            if goodsub.has_node(b):
                goodsub.node[b]['color'] = 'cyan'
        goodsub.node[good]['color'] = 'red'
        plt.subplot(121)
        nx.draw_graphviz(goodsub, with_labels=False, node_color=[goodsub.node[n]['color'] for n in goodsub.nodes()],
                       edge_color=[cmap(edge[2]['weight']/emax) for edge in goodsub.edges(data=True)],
                       alpha=0.5)
        badsub = net.subgraph([bad] + net.predecessors(bad)).copy()
        for b in odd_cells:
            if badsub.has_node(b):
                badsub.node[b]['color'] = 'cyan'
        badsub.node[bad]['color'] = 'red'
        plt.subplot(122)
        nx.draw_graphviz(badsub, with_labels=False, node_color=[badsub.node[n]['color'] for n in badsub.nodes()],
                       edge_color=[cmap(edge[2]['weight']/emax) for edge in badsub.edges(data=True)],
                       alpha=0.5)        
        plt.show()
        
def plot_burst_intervals_in_datalist(datalist):        
    for data in datalist:
        plot_burst_intervals(data)
        spin_stell_count = int(dict(data.fdata['runconfig/cellcount'])['SpinyStellate'])
        stim_times = data.get_bgstim_times()
        value = np.ones(len(stim_times)) * spin_stell_count
        plt.plot(stim_times,value , 'gv')
        plt.show()

def compare_oddcell_nets_from_datalist(datalist):
    for data in datalist:
        plot_odd_cells(data)

def plot_conn_strengths(data):
    ibi = data.get_pop_ibi('SpinyStellate')
    odd_cells = list(ibi['odd_cells'])
    cells = [ss for ss in data.spikes.keys() if ss.startswith('Spin')]
    good_cells = list(set(cells) - set(odd_cells))
    post_cell = [dest.split('_')[0] for dest in data.fnet['/network/synapse']['dest']]
    ampa = defaultdict(float)
    gaba = defaultdict(float)
    nmda = defaultdict(float)
    # collect total incoming synaptic conductances to each cell
    # for each synapse type
    synapse = data.fnet['/network/synapse']
    ampa_idx = np.nonzero(synapse['type'] == 'ampa')[0]
    ampa_dests = [dest[0] for dest in np.char.split(synapse['dest'][ampa_idx], '/')]
    ampa_weights = synapse['Gbar'][ampa_idx].copy()
    for d, w in zip(ampa_dests, ampa_weights):
        ampa[d] += w
    nmda_idx = np.nonzero(synapse['type'] == 'nmda')[0]
    nmda_dests = [dest[0] for dest in np.char.split(synapse['dest'][nmda_idx], '/')]
    nmda_weights = synapse['Gbar'][nmda_idx].copy()
    for d, w in zip(nmda_dests, nmda_weights):
        nmda[d] += w
    gaba_idx = np.nonzero(synapse['type'] == 'gaba')[0]
    gaba_dests = [dest[0] for dest in np.char.split(synapse['dest'][gaba_idx], '/')]
    gaba_weights = synapse['Gbar'][gaba_idx].copy()
    for d, w in zip(gaba_dests, gaba_weights):
        gaba[d] += w
    ampa_list = [ampa[cell] for cell in odd_cells + good_cells]
    nmda_list = [nmda[cell] for cell in odd_cells + good_cells]
    gaba_list = [gaba[cell] for cell in odd_cells + good_cells]
    x1 = np.arange(len(odd_cells))
    x2 = np.arange(len(odd_cells), len(cells), 1)

    print len(cells), len(good_cells), len(odd_cells)
    print len(set(odd_cells))
    plt.plot(x1, ampa_list[:len(odd_cells)], 'gx', label='AMPA - odd cells')
    plt.plot(x2, ampa_list[len(odd_cells):], 'g+', label='AMPA - normal cells')
    plt.plot(np.arange(len(odd_cells)), nmda_list[:len(odd_cells)], 'bx', label='NMDA - odd cells')
    plt.plot(np.arange(len(odd_cells), len(cells)), nmda_list[len(odd_cells):], 'b+', label='NMDA - normal cells')
    plt.plot(np.arange(len(odd_cells)), gaba_list[:len(odd_cells)], 'rx', label='GABA - odd cells')
    plt.plot(np.arange(len(odd_cells), len(cells)), gaba_list[len(odd_cells):], 'r+', label='GABA - normal cells')
    plt.legend()
    plt.show()

from scipy.cluster.vq import whiten, kmeans2

def get_chan_density(data, celltype, compartment):
    """Get the channel density matrix for cells of type cell type.

    Returns a 3-tuple: (cells, channels, G)

    where cells is list of cells

    channels is list of channels

    G is an len(cells)xlen(channels) array where G[i][j] is Gbar of
    channels[j] of cell[i] in `compartment`.

    """
    hhchaninfo = np.asarray(data.fnet['/network/hhchan'])    
    cell_pattern = '/model/net/%s_' % (celltype)    
    indices = np.char.startswith(hhchaninfo['f0'], cell_pattern)
    ss_data = hhchaninfo[indices].copy()
    soma_indices = np.nonzero(np.char.rfind(ss_data['f0'], '/%s/' % (compartment)) != -1)[0] # Get the indices containing soma data
    ss_data = ss_data[soma_indices].copy()
    # token[0] is '', token[1] is 'model', token[2] is 'net', token[3] is cell name, last token is channel name, the compartment is already soma    
    ss_gk = defaultdict(lambda : defaultdict(float))
    channels = {}
    for index, token in enumerate(np.char.split(ss_data['f0'], '/')):
        ss_gk[token[3]][token[-1]] = ss_data['f1'][index]
        if token[-1] not in channels:
            channels[token[-1]] = True
    numcells = len(ss_gk)
    data_array = np.zeros((numcells, len(channels)))
    for cidx, d in enumerate(ss_gk.values()):
        for chidx, chan in enumerate(channels):
            data_array[cidx, chidx] = d[chan]
    return ss_gk.keys(), channels.keys(), data_array
    

def clustering_on_conductance(data, celltype):
    """Do a clustering based on various channel conductances in soma"""
    cells, channels, data_array = get_chan_density(data, celltype, 'comp_1')
    whitened = whiten(data_array)
    centroid, labels = kmeans2(whitened, 20)
    plt.plot(np.arange(len(labels)), labels, 'x')
    plt.show()

def plot_pop_spike_hist(data):
    bgtimes = data.get_bgstim_times()
    cells, hist, bins = data.get_pop_spike_hist('SpinyStellate')
    plt.bar(bins[:-1], hist, np.ones(len(hist)) * (bins[1] - bins[0]), linewidth=0)
    plt.plot(bgtimes, -np.ones(len(bgtimes)), 'g^')
    plt.title('%s: %s' % (data.fdata.filename, dict(data.fdata['/runconfig/stimulus'])['bg_count']))
    plt.show()


from sklearn.cluster import AffinityPropagation
from sklearn import metrics
from itertools import combinations, cycle
def do_affinity_cluster_on_somatic_density(data, celltype):
    # I am getting the odd cells for comparing with each cluster
    cats = data.get_pop_ibi('SpinyStellate')
    odd_cells = set(cats['odd_cells'])    
    # till here - is not really necessary
    cells, channels, data_array = get_chan_density(data, celltype, 'comp_1')
    max_odd_overlap = 0
    max_odd_combo = None
    for r in range(2, data_array.shape[1]):
        it = combinations(range(data_array.shape[1]), r)
        for ii in it:
            sub_array = data_array[:, ii]
            af = AffinityPropagation().fit(sub_array)
            cluster_centers_indices = af.cluster_centers_indices_
            labels = af.labels_    
            n_clusters_ = len(cluster_centers_indices)   
            labeled_cells = defaultdict(list)
            for idx, ll in enumerate(labels):
                labeled_cells[ll].append(cells[idx])
            print 'Overlap with odd cells:'
            for ll, cl in labeled_cells.items():
                overlap = set(cl).intersection(odd_cells)
                print 'label: %d: %d out of %d in cluster and %d in odd_cells' % (ll, len(overlap),
                                                                       len(cl),
                                                                       len(odd_cells))
                if len(overlap) > max_odd_overlap:
                    max_odd_overlap = len(overlap)
                    max_odd_combo = [channels[jj] for jj in ii]
            print 'Estimated number of clusters: %d' % n_clusters_
            print ("Silhouette Coefficient: %0.3f" %
                   metrics.silhouette_score(data_array, labels, metric='sqeuclidean'))
            # import pylab as pl
            # pl.close('all')
            # pl.figure(1)
            # pl.clf()

            # colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
            # for k, col in zip(range(n_clusters_), colors):
            #     class_members = labels == k
            #     cluster_center = sub_array[cluster_centers_indices[k]]
            #     pl.plot(sub_array[class_members, 0], sub_array[class_members, 1], col + '.')
            #     pl.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col,
            #             markeredgecolor='k', markersize=14)
            #     for x in sub_array[class_members]:
            #         pl.plot([cluster_center[0], x[0]], [cluster_center[1], x[1]], col)
            # title = 'Estimated number of clusters: %d\nParameters:' % (n_clusters_)
            # for jj in ii:
            #     title += channels[jj] + ','
            # pl.title(title)
            # pl.show()
    print data.fdata.filename
    print 'No of odd cells:', len(odd_cells)
    print 'Maximum overlap with odd cells:', max_odd_overlap, 'for channels:', max_odd_combo
    return labeled_cells
        

if __name__ == '__main__':
    colordict = util.get_celltype_colors()
    datalist = []
    with open('exc_inh_stim_balance_20121224.txt') as flistfile:
        for line in flistfile:
            fname = line.strip()
            if fname.startswith('#') or len(fname) == 0:
                continue
            data = TraubData(fname)
            plot_pop_spike_hist(data)
                


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
