# probabilities.py --- 
# 
# Filename: probabilities.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Mon Mar 19 23:25:51 2012 (+0530)
# Version: 
# Last-Updated: Mon Apr  2 16:11:03 2012 (+0530)
#           By: subha
#     Update #: 1606
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

from collections import defaultdict

import os
import numpy as np
import h5py as h5
import igraph as ig
from datetime import datetime
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def update_pyplot_config():
    params = {'font.size' : 10,
          'axes.labelsize' : 10,
          'font.size' : 10,
          'text.fontsize' : 10,
          'legend.fontsize': 10,
          'xtick.labelsize' : 8,
          'ytick.labelsize' : 8}
    plt.rcParams.update(params)

excitatory_celltypes = [
    'SupPyrRS',
    'SupPyrFRB',
    'SpinyStellate',
    'TuftedIB',
    'TuftedRS',
    'NontuftedRS',
    'TCR'
    ]

WINDOWS = [10e-3, 20e-3, 30e-3, 40e-3]
DELAYS = [0.0, 10e-3, 20e-3, 30e-3, 40e-3]
class SpikeCondProb(object):
    def __init__(self, datafilepath, netfilepath=None, netfilepath_new=None):
        self.datafile = h5.File(datafilepath, 'r')
        if netfilepath is None:
            netfilepath = datafilepath.replace('/data_', '/network_')

        self.netfile = h5.File(netfilepath, 'r')

        if netfilepath_new is None:
            netfilepath_new = netfilepath.replace('.h5', '.h5.new')
            print 'Crearting netfile_new path:', netfilepath_new

        try:
            self.netfile_new = h5.File(netfilepath_new, 'r')
            print 'Opened', self.netfile_new.filename
        except IOError:
            print 'Warning: no network file in new format:', 
            self.netfilepath_new = None

        self.schedinfo = {}
        for row in self.datafile['/runconfig/scheduling']:
            try:
                value = float(row[1])
                self.schedinfo[row[0]] = value
            except ValueError:
                pass
        # A few boolean variables to keep track of what operations are possible on this set of data
        self.valid_bg_stimulus = True        
        self.valid_probe_stimulus = True     
        self._bg_shortest_paths = None
        self._probe_shortest_paths = None
        self.__check_validities()
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
        if hasattr(self, 'stimprobfile'):
            self.stimprobfile.close()
            
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
        if not self.valid_bg_stimulus or not self.valid_probe_stimulus:
            return
        self.bg_stim = self.datafile['stimulus/stim_bg'][:]
        self.probe_stim = self.datafile['stimulus/stim_probe'][:]
        self.bg_times = (np.nonzero(np.diff(self.bg_stim) < 0)[0] + 1.0) * self.schedinfo['simdt'] # extract the indices where bg stim went from hi->lo
        self.probe_times = (np.nonzero(np.diff(self.probe_stim) < 0)[0] + 1.0) * self.schedinfo['simdt']
        self.bg_targets = []
        self.probe_targets = []
        stimdata = self.netfile_new['/stimulus/connection'][:]
        bg_indices = np.char.equal(stimdata['f0'], '/stim/stim_bg')
        # The target compartment path is saved in field[1], which has the form: /model/net/cell/comp
        # split('/') will return ['', 'model', 'net', 'cell', 'comp']
        self.bg_targets = [token[3] for token in np.char.split(stimdata['f1'][bg_indices], '/')]
        probe_indices = np.char.equal(stimdata['f0'], '/stim/stim_probe')
        self.probe_targets = [token[3] for token in np.char.split(stimdata['f1'][probe_indices], '/')]
        print 'Background stimulus targets', self.bg_targets
        print 'Probe stimulus targets', self.probe_targets
            
        

    def __check_validities(self):
        try:
            connset = self.netfile_new['stimulus/connection'][:]
            if len(connset) == 0:
                self.valid_bg_stimulus = False
                self.valid_probe_stimulus = False
        except KeyError:
            self.valid_bg_stimulus = False
            self.valid_probe_stimulus = False

        if not self.valid_bg_stimulus:
            print 'Warning: this data does not have any stimulus connected to cells:', self.datafile.filename
        bgstim = self.datafile['/stimulus/stim_bg'][:]
        if len(np.nonzero(np.diff(bgstim)<0)[0]) == 0:
            print 'Warning: No background stimulus applied in this dataset:', self.datafile.filename
            self.valid_bg_stimulus = False
        probestim = self.datafile['/stimulus/stim_probe'][:]
        if len(np.nonzero(np.diff(probestim)<0)[0]) == 0:
            print 'Warning: No probe stimulus applied in this dataset:', self.datafile.filename
            self.valid_probe_stimulus = False
        print 'Probe stimulus valid?', self.valid_probe_stimulus
        print 'Background stimulus valid?', self.valid_bg_stimulus
        
        
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
        if not self.valid_bg_stimulus:
            return -1.0
        bg_spike_prob = 0
        only_bg_count = len(self.bg_times) - len(self.probe_times)
        if only_bg_count <= 0:
            return -1.0
        # print 'bg_times', self.bg_times
        ii = 0
        while ii  < len(self.bg_times):
            win_start = self.bg_times[ii] + delay
            win_end = win_start + width
            # print win_start, win_end
            spike_count = np.nonzero((self.spikes[cell] > win_start) & 
                                     (self.spikes[cell] <= win_end))[0]
            # print spike_count
            if len(spike_count) > 0:
                bg_spike_prob += 1.0
            ii += 2
        return bg_spike_prob / only_bg_count

    def calc_spikecount_avg_after_bgstim(self, cell, width, delay):
        """Calculate the probability of spike following a background
        stimulus"""    
        if not self.valid_bg_stimulus:
            return -1.0
        spike_count = 0.0
        only_bg_count = len(self.bg_times) - len(self.probe_times)
        if only_bg_count <= 0:
            return -1.0
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
        if not self.valid_probe_stimulus:
            return -1.0
        probe_spike_prob = 0
        # print 'probe_times:', self.probe_times
        for ii in range(len(self.probe_times)):
            win_start = self.probe_times[ii] + delay
            win_end = win_start + width
            # print win_start, win_end
            spike_count = np.nonzero((self.spikes[cell] > win_start) & 
                                      (self.spikes[cell] <= win_end))[0]
            if len(spike_count) > 0:
                probe_spike_prob += 1.0
        return probe_spike_prob / len(self.probe_times)

    def calc_spikecount_avg_after_probestim(self, cell, width, delay):
        """Calculate the probability of spike following a background
        stimulus"""
        if not self.valid_probe_stimulus:
            return -1.0
        spike_count = 0.0
        for ii in range(len(self.probe_times)):
            spike_count += len(np.nonzero((self.spikes[cell] > (self.probe_times[ii] + delay)) & 
                                      (self.spikes[cell] <= (self.probe_times[ii] + delay + width)))[0])
        return spike_count / len(self.probe_times)

    def dump_stim_p(self, windowlist, delaylist, overwrite=False):
        outfilepath = self.datafile.filename.replace('/data_', '/stim_prob_')
        if not os.path.exists(outfilepath) or overwrite:
            if hasattr(self, 'stimprobfile'):
                self.stimprobfile.close()
            self.stimprobfile = h5.File(outfilepath, 'w')
            grp = self.stimprobfile.create_group('/spiking_prob')
            grp.attrs['NOTE'] = 'prob_bg is probability of spiking after \
only background stimulus. prob_probe is that after background + probe stimulus. \
spike_avg_bg is the average spike count after background only stimulus. \
spike_avg_probe is teh average spike count after background + probe.'            
            ii = 0
            for window in windowlist:
                jj = 0
                for delay in delaylist:
                    bg_p = [self.calc_spike_prob_after_bgstim(cell, window, delay) for cell in self.cells]
                    probe_p = [self.calc_spike_prob_after_probestim(cell, window, delay) for cell in self.cells]
                    bg_spikeavg = [self.calc_spikecount_avg_after_bgstim(cell, window, delay) for cell in self.cells]
                    probe_spikeavg = [self.calc_spikecount_avg_after_probestim(cell, window, delay) for cell in self.cells]
                    data = zip(self.cells, bg_p, probe_p, bg_spikeavg, probe_spikeavg)
                    dtype = np.dtype([('cell', '|S35'), ('prob_bg', 'f4'), ('prob_probe', 'f4'), ('spike_avg_bg', 'f4'), ('spike_avg_probe', 'f4')])
                    data = np.asarray(data, dtype=dtype)
                    dset = grp.create_dataset('prob_window_%d_delta_%d' % (ii, jj), data=data)
                    dset.attrs['delay'] = delay
                    dset.attrs['window'] = window
                    jj += 1
                ii += 1
            self.stimprobfile.close()
            self.stimprobfile = h5.File(outfilepath, 'r')
        if not hasattr(self, 'stimprobfile'):
            self.stimprobfile = h5.File(outfilepath, 'r')
        
    def get_stim_p(self, celltype='', windows=WINDOWS, delays=DELAYS, overwrite=False):
        """Calculate the stimulus linked probability increase due to
        probe stimulus from background for each window sizes at all
        given delays."""        
        ret = []
        # Now actually load and return the data
        if not hasattr(self, 'stimprobfile') or self.stimprobfile is None:
           self.dump_stim_p(windows, delays, overwrite)
        grp = self.stimprobfile['spiking_prob']
        cells = None
        cellindices = None
        for dsetname in grp:
            dset = grp[dsetname]
            delay = dset.attrs['delay']
            window = dset.attrs['window']
            # print 'Original dataset:', delay, window
            delay_in = False
            for entry in delays:
                if np.allclose([delay], [entry]):
                    delay_in = True
                    break
            window_in = False
            for entry in windows:
                if np.allclose([window], [entry]):
                    window_in = True
                    break
            if  (len(delays) == 0) or (len(windows) == 0) or (window_in and delay_in):
                data = dset[:]
            else:
                continue
            if cells is None:
                cells = data['cell']
                cellindices = np.nonzero(np.char.startswith(cells, celltype))[0]
                cells = cells[cellindices]
            bgp = data[cellindices]['prob_bg']
            assert(bgp.shape == cells.shape)
            if max(bgp) == 0.0:
                print 'Warning:', self.datafile.filename, ', window:', window, ', delay:', delay, ': bgp is all 0'
            probep = data[cellindices]['prob_probe']
            assert(probep.shape == cells.shape)
            if max(probep) == 0.0:
                print 'Warning:', self.datafile.filename, ', window:', window, ', delay:', delay, ': probep is all 0'            
            ret.append((window, delay, bgp, probep))
        return (cells, ret)

    def get_stim_del_p(self, celltype='', windows=WINDOWS, delays=DELAYS, overwrite=False):
        """Goes through stimulus linked probability file and picks up
        the window delay and increase in probability from
        background-only to background+probe stimulus

        If celltype is specified, does this for only that celltype,
        for all cells otherwise.

        If overwrite is True then it recomputes all the proebabilities
        and overwrites existing file.

        Return (list of cells, list of tuples each containing window,
        delay, list of del P (probe-bg) corresponding to the list of
        cells).

        """
        WINDOW = 0
        DELAY = 1
        BGP = 2
        PROBEP = 3
        ret = []
        if not self.valid_probe_stimulus or not self.valid_bg_stimulus:
            return ret
        # We calculate the following default case with window
        # sizes increasing by 10 ms and 0 delay.
        cells, datalist, = self.get_stim_p(celltype, windows, delays, overwrite)
        for data in datalist:
            ret.append((data[WINDOW], data[DELAY], data[PROBEP] - data[BGP]))
        return (cells, ret)

    def get_bg_shortest_path_lengths(self):
        """Returns a dictionary of dictionaries mapping
        backgroun-stimulust-target to each cell to the length of the
        shortest patrh between them.

        Thus ret[x][y] == k where k is the the shortest distance from
        vertex with index x to vertex with index y, where x the vertex
        index of a cell stimulated by the background stimulus.
        """
        if hasattr(self, 'bg_path_lengths') and self.bg_path_lengths is not None:
            return self.bg_path_lengths
        self.bg_vertices = self.ampa_graph.vs.select(name_in=self.bg_targets)
        self.bg_path_lengths = defaultdict(dict)
        if self._bg_shortest_paths is None:
            self._bg_shortest_paths = {}
            for vv in self.bg_vertices:
                paths = self.ampa_graph.get_all_shortest_paths(vv.index, mode=ig.OUT)
                self._bg_shortest_paths[vv['name']] = paths
                for path in paths:
                    self.bg_path_lengths[vv.index][path[-1]] = len(path) - 1

        return self.bg_path_lengths
        
    def get_probe_shortest_path_lengths(self):
        """Calculate the shortest paths from probe cells to every
        other cell.

        Return a dictionary of dictionaries. self.bg_path[v1][v2] ==
        pathlength from vertex with index v1 to that with index v2.
        """
        if hasattr(self, 'probe_path_lengths'):
            return self.probe_path_lengths
        self.probe_vertices = self.ampa_graph.vs.select(name_in=self.probe_targets)
        self.probe_path_lengths = defaultdict(dict)
        if self._probe_shortest_paths is None:
            self._probe_shortest_paths = {}
            for vv in self.probe_vertices:
                paths = self.ampa_graph.get_all_shortest_paths(vv.index, mode=ig.OUT)
                self._probe_shortest_paths[vv['name']] = paths
                for path in paths:
                    self.probe_path_lengths[vv.index][path[-1]] =  len(path) - 1
        return self.probe_path_lengths

    def calc_stim_shortest_distance_del_p_correlation(self, celltype='', windows=WINDOWS, delays=DELAYS, overwrite=False):
        """Correlate the shortest distance of a cell from the
        stimulated set. This does not (yet) take synaptic strength
        into account."""
        ret = []
        probepathlenmap = self.get_probe_shortest_path_lengths()        
        cells, del_p_list, = self.get_stim_del_p(celltype, windows, delays, overwrite)
        vseq = [self.ampa_graph.vs.select(name_eq=cell)[0] for cell in cells]
        probeshortest = []
        # Collect the shortest of the distances to cells in the
        # probe-stimulated set in the same order as in del_p list
        ii = 0
        probeshortest = np.ones(len(cells)) * np.inf
        for vtarget in vseq:            
            for vprobe in self.probe_vertices:                
                try:
                    new_val = probepathlenmap[vprobe.index][vtarget.index]
                    if new_val < probeshortest[ii]:
                        probeshortest[ii] = new_val
                except KeyError:
                    print "Cell pair not connected:", vprobe['name'], vtarget['name']
                    # print 'Vertex connectivity:', self.ampa_graph.vertex_connectivity(vprobe.index, vtarget.index)            
            ii += 1
        mask = np.nonzero(probeshortest < np.inf)[0]
        for (window, delay, del_p) in del_p_list:
            if max(del_p) == 0.0:
                print 'Warning:', self.datafile.filename, ', window:', window, ', delay:', delay, ': del_p is all zero'
                continue
            plt.plot(probeshortest[mask], del_p[mask], 'x')
            plt.show()
            corrcoef = np.corrcoef(probeshortest[mask], del_p[mask])
            # corrcoef is a 2x2 matrix for 1 D arrays where the
            # antidiagonal elements correspond to cross coreelation
            # and diagonal elements are autocorrelation. So we take
            # the first antidiagonal element (the other is identical).
            ret.append((window, delay, corrcoef[0,1]))
        return (cells, ret)

    def calc_stim_distance_del_p_corrrelation(sellf, celltype='', windows=WINDOWS, delay=DELAYS, overwrite=False):
        """Correlate the distance to the probe stimulated cells to
        del_p. I measure the distance as resistance in parallel:
        
        1/equivalent = 1/d1 + 1/d2 + 1/d3 + ...

        The situation is intuitively similar to parallel resistors
        where each different path gives an additional route for signal
        to reach the target."""
        probepathlenmap = {}
        for cell, pathlengths in self.__calc_probe_shortest_paths().items():
            probepathlenmap[cell] = 1.0/sum([1.0/length for length in pathlengths])
        raise(NotImplementedError, 'TODO: finish this function def')
            
    
                                
        
        

def check_valid_files(filenames, celltype):
    valid = []
    invalid = []
    for name in filenames:
        df = h5.File(name, 'r')
        data = [np.asarray(df['spiking_prob'][dset]) for dset in df['spiking_prob']]
        ss_bg_prob = dict([(row[0], row[1]) for row in data[0] if row[0].startswith(celltype)])
        orig_data_file_name = name.replace('stim_prob_', 'data_')
        odf = h5.File(orig_data_file_name, 'r')
        stim = odf['/stimulus/stim_bg'][:]
        if max(ss_bg_prob.values()) == -1.0:
            invalid.append(odf.filename)
            if len(np.nonzero(np.diff(stim)<0)[0]) > 0:
                print 'Warning:', odf.filename, 'has stimulus but no related spike'
            else:
                print df.filename, 'has no stimulus'
        else:
            if len(np.nonzero(np.diff(stim)<0)) == 0:
                print 'Warning:', odf.filename, 'has NO stimulus but stim related spikes. Look for inconsistencies.'
            else:
                valid.append(df.filename)
        df.close()
        odf.close()
    return (valid, invalid)
            

from matplotlib import pyplot 

def display_probability_plots(filelistfile, celltype):
    """Display the peristimulus spiking probability values for cells
    of celltype"""
    probability_files = [line.strip() for line in open(filelistfile, 'r')]
    valid_files, invalid_files, = check_valid_files(probability_files, celltype)
    for filename in valid_files:
        dataf = h5.File(filename, 'r')
        num_datasets = len(dataf['spiking_prob'])
        rowcount = int(num_datasets / 2.0 + 0.5)        
        plotindex = 1
        plt.figure(figsize=(8,11))
        plt.clf()
        for dataset_name in dataf['spiking_prob']:
            dataset = dataf['spiking_prob'][dataset_name]
            delay = dataset.attrs['delay']
            window = dataset.attrs['window']
            data = dataset[:]
            cell_indices = np.nonzero(np.char.startswith(data['cell'], celltype))[0]
            bgp = data['prob_bg'][cell_indices]     
            bg_indices = np.nonzero(bgp >=0)[0]
            probep = data['prob_probe'][cell_indices][bg_indices]
            probe_indices = np.nonzero(probep >=0)[0]
            bgp = bgp[probe_indices]
            probep = probep[probe_indices]
            deltap = probep - bgp
            plt.subplot(rowcount, 2, plotindex)
            plotindex += 1
            plt.bar(np.arange(0,len(deltap), 1.0), deltap)
            plt.title('delay:%g width:%g' % (delay, window))
            # plt.legend()
        plt.suptitle('P(spike/probe) - P(spike/background)\nFile: %s' % (filename))
        figfile = '%s' % (filename.replace('.h5', '.png').replace('stim_prob_', 'stim_delprob_%s' % (celltype)))
        plt.savefig(figfile)
        print 'Figure saved in:', figfile        
        dataf.close()
        plt.show()
        
def display_delp_with_distance(filelistfile, celltype):
    """Display the correlation between distance from probe-stimulated
    cells and increase in spiking probability due to probe
    stimulus."""
    probability_files = [line.strip() for line in open(filelistfile, 'r')]
    valid_files, invalid_files, = check_valid_files(probability_files, celltype)
    for filename in valid_files:
        netf = h5.File(filename.replace('stim_prob_', 'network_').replace('.h5', '.h5.new'), 'r')
        stimdata = netf['/stimulus/connection'][:]
        bg_indices = np.char.equal(stimdata['f0'], '/stim/stim_bg')
        # The target compartment path is saved in field[1], which has the form: /model/net/cell/comp
        bg_targets = [token[2] for token in np.char.split(stimdata['f1'][bg_indices], '/')]
        probe_indices = np.char.equal(stimdata['f0'], '/stim/stim_probe')
        probe_targets = [token[2] for token in np.char.split(stimdata['f1'][probe_indices], '/')]
        probf = h5.File(filename, 'r')
        num_datasets = len(dataf['spiking_prob'])
        rowcount = int(num_datasets / 2.0 + 0.5)        
        plotindex = 1
        plt.figure(figsize=(8,11))
        plt.clf()
        for dataset_name in probf['spiking_prob']:
            dataset = dataf['spiking_prob'][dataset_name]
            delay = dataset.attrs['delay']
            window = dataset.attrs['window']
            data = dataset[:]
            cell_indices = np.nonzero(np.char.startswith(data['cell'], celltype))[0]
            bgp = data['prob_bg'][cell_indices]     
            bg_indices = np.nonzero(bgp >=0)[0]
            probep = data['prob_probe'][cell_indices][bg_indices]
            probe_indices = np.nonzero(probep >=0)[0]
            bgp = bgp[bg_indices][probe_indices]
            probep = probep[probe_indices]
            deltap = probep - bgp
            cells = data['cell'][cell_indices][bg_indices][probe_indices]
            plt.subplot(rowcount, 2, plotindex)
            plotindex += 1
            plt.bar(np.arange(0,len(deltap), 1.0), deltap)
            plt.title('delay:%g width:%g' % (delay, window))
            # plt.legend()
        plt.suptitle('P(spike/probe) - P(spike/background)\nFile: %s' % (filename))
        figfile = '%s' % (filename.replace('.h5', '.png').replace('stim_prob_', 'stim_delprob_%s' % (celltype)))
        plt.savefig(figfile)
        print 'Figure saved in:', figfile        
        dataf.close()
        plt.show()
    

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
            figure = plt.figure()
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
                axes = plt.subplot(rows, cols, ii+1)
                plt.hist(data, bins=np.arange(0, 1.1, 0.1), normed=True, histtype='bar', label=labels)
                plt.legend(prop={'size':'xx-small'})
                plt.ylim([0, 10.0])
                plt.xlim([0, 1.1])
                axes = plt.subplot(rows, cols, ii+2)
                plt.hist(data, bins=np.arange(0, 1.1, 0.1), normed=True, histtype='step', cumulative=True, label=labels)
                plt.legend(prop={'size':'xx-small'})
                plt.ylim([0, 10.0])
                plt.xlim([0, 1.1])
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
                
def dump_stimulus_linked_probabilities(datafilelist, windowlist, delaylist):
    netfilelist = [line.strip().replace('/data_', '/network_') for line in datafilelist]
    for datafilepath, netfilepath in zip(datafilelist, netfilelist):
        outfilepath = datafilepath.replace('/data_', '/stim_prob_')
        print 'Outfilepath:', outfilepath
        plotfilepath = datafilepath.replace('/data_', '/stim_hist_').replace('.h5', '.pdf')
        print 'Plotfile path:', plotfilepath
        dataout = h5.File(outfilepath, 'w')
        grp = dataout.create_group('/spiking_prob')
        grp.attrs['NOTE'] = 'Probability of spiking after a stimulus within a specified time window.'
        plotfile = PdfPages(plotfilepath)
        prob_counter = SpikeCondProb(datafilepath, netfilepath)
        ii = 0        
        for window in windowlist:
            jj = 0
            for delay in delaylist:
                prob_post_bg = [prob_counter.calc_spike_prob_after_bgstim(cell, window, delay) for cell in prob_counter.cells]
                prob_post_probe = [prob_counter.calc_spike_prob_after_probestim(cell, window, delay) for cell in prob_counter.cells]
                spike_avg_post_bg = [prob_counter.calc_spikecount_avg_after_bgstim(cell, window, delay) for cell in prob_counter.cells]
                spike_avg_post_probe = [prob_counter.calc_spikecount_avg_after_probestim(cell, window, delay) for cell in prob_counter.cells]
                # Save data into hdf5 file
                data = zip(prob_counter.cells, prob_post_bg, prob_post_probe, spike_avg_post_bg, spike_avg_post_probe)
                dtype=np.dtype([('cell', '|S35'), ('prob_bg', 'f4'), ('prob_probe', 'f4'), ('spike_avg_bg', 'f4'), ('spike_avg_probe', 'f4')])
                array_data = np.asarray(data, dtype=dtype)
                dataset = grp.create_dataset('prob_window_%d_delta_%d' % (ii, jj), data=array_data)
                dataset.attrs['delay'] = delay
                dataset.attrs['window'] = window
                if len(prob_post_probe) == 0 or min(prob_post_probe) == max(prob_post_probe):
                    continue
                # Now plot the data
                figure = plt.figure()
                plt.title('window: %g, delay: %g' % (window, delay))                
                plt.hist([prob_post_bg, prob_post_probe], bins=np.arange(0, 1.1, 0.1), normed=True, histtype='bar', label=['prob-bg', 'prob-probe'])
                plt.ylim([0.0, 10.0])
                plt.xlim([0.0, 1.1])
                plt.legend(prop={'size':'xx-small'})
                # plt.show()
                print 'finished delay:', delay
                plotfile.savefig(figure)
                figure.clf()
                jj += 1
            ii += 1
            print 'finished window:', window
        print 'Finished', netfilepath, datafilepath
        plotfile.close()
        dataout.close()

def do_run_dump_stimulus_linked_probabilities(filelistfile):
    files = [line.strip() for line in open(filelistfile, 'r')]
    windows = np.arange(0, 0.05, 10e-3)
    dump_stimulus_linked_probabilities(files, windows, [0.0])

import sys
    
if __name__ == '__main__':
    df = '2012_03_22/data_20120322_114922_24526.h5'    
    sp = SpikeCondProb(df)
    x = sp.calc_stim_shortest_distance_del_p_correlation('SpinyStellate', windows=WINDOWS, delays=DELAYS, overwrite=True)
    for window, delay, correlation in x[1]:
        print 'Window:', window, 'Delay:', delay, 'CorrCoef:', correlation
    # do_run_dump_stimulus_linked_probabilities(sys.argv[1])
    # test_main()
    # if len(sys.argv) < 3:
    #     print 'Usage:', sys.argv[0], 'filelist mode'
    #     print 'where file list is a text file with one data file path in each line. mode can be \'pre\' or \'post\'. Dumps pre/post synaptic spike probabilities from spike train data.'
    #     sys.exit(0)
    # files = [line.strip().replace('.new', '') for line in open(sys.argv[1], 'r')]
    # if sys.argv[2] == 'pre':
    #     delays = np.arange(11e-3, 51e-3, 10e-3)
    # else:
    #     delays = np.arange(1e-3, 41e-3, 10e-3)

    # run_on_files(files, [10e-3], delays, sys.argv[2])
    
# 
# probabilities.py ends here
