# probabilities.py --- 
# 
# Filename: probabilities.py
# Description: 
# Author: Subhasis Ray
# Maintainer: 
# Created: Mon Mar 19 23:25:51 2012 (+0530)
# Version: 
# Last-Updated: Mon Apr  2 09:50:01 2012 (+0530)
#           By: subha
#     Update #: 1416
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
from matplotlib import pyplot    
from matplotlib.backends.backend_pdf import PdfPages

def update_pyplot_config():
    params = {'font.size' : 10,
          'axes.labelsize' : 10,
          'font.size' : 10,
          'text.fontsize' : 10,
          'legend.fontsize': 10,
          'xtick.labelsize' : 8,
          'ytick.labelsize' : 8}
    pyplot.rcParams.update(params)

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

        if netfilepath_new is None:
            netfilepath_new = netfilepath.replace('.h5', '.h5.new')

        try:
            self.netfile_new = h5.File(netfilepath_new, 'r')
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
        
    def get_stim_p(self, celltype='', windowlist=[], delaylist=[], overwrite=False):
        """Calculate the stimulus linked probability increase due to
        probe stimulus from background for each window sizes at all
        given delays."""        
        ret = []
        # Now actually load and return the data
        if not hasattr(self, 'stimprobfile') or self.stimprobfile is None:
           self.dump_stim_p(windowlist, delaylist, overwrite)
        grp = self.stimprobfile['spiking_prob']
        cells = None
        for dsetname in grp:
            dset = grp[dsetname]
            delay = dset.attrs['delay']
            window = dset.attrs['window']
            if not delaylist or not windowlist or (delay in delaylist and window in windowlist):
                data = dset[:]
            else:
                continue
            cellindices = np.nonzero(np.char.startswith(data['cell'], celltype))[0]
            bgp = data[cellindices]['prob_bg']
            bgindices = np.nonzero(bgp >= 0.0)[0]
            probep = data[cellindices]['prob_probe'][bgindices]
            probeindices = np.nonzero(probep >= 0.0)[0]
            bgp = bgp[bgindices][probeindices]
            probep = probep[probeindices]
            if cells is None:
                cells = data[cellindices][bgindices][probeindices]['cell']
            ret.append((window, delay, bgp, probep))
        return (cells, ret)

    def get_stim_del_p(self, celltype='', windows=[10e-3, 20e-3, 30e-3, 40e-3, 50e-3], delays=[0.0], overwrite=False):
        """Goes through stimulus linked probability file and picks up
        the window delay and increase in probability from
        background-only to background+probe stimulus

        If celltype is specified, does this for only that celltype,
        for all cells otherwise.

        If overwrite is True then it recomputes all the proebabilities
        and overwrites existing file.

        Return  (list of cells, list of tuples each containing window, delay, list of del P (probe-bg) corresponding to the list of
        cells).

        """
        WINDOW = 0
        DELAY = 1
        BGP = 2
        PROBEP = 3
        ret = []
        if not self.valid_probe_stimulus or not self.valid_bg_stimulus:
            return ret
        if overwrite or not hasattr(self, 'stimprobfile'):
            # We calculate the following default case with window
            # sizes increasing by 10 ms and 0 delay.
            cells, datalist, = self.get_stim_p(celltype, windows, delays, overwrite)
        for data in datalist:
            ret.append((data[WINDOW], data[DELAY], data[PROBEP] - data[BGP]))
        return (cells, ret)

    def get_bg_shortest_path_lengths(self):
        if hasattr(self, 'bg_paths'):
            return self.bg_paths
        self.bg_vertices = self.ampa_graph.vs.select(name_in=self.bg_targets)
        self.bg_paths = defaultdict(dict)
        if self._bg_shortest_paths is None:
            self._bg_shortest_paths = {}
            for vv in self.bg_vertices:
                paths = self.ampa_graph.get_all_shortest_paths(vv.index, mode=ig.OUT)
                self._bg_shortest_paths[vv['name']] = paths
                for path in paths:
                    self.bg_paths[vv.index][path[-1]] = len(path) - 1
        
    def get_probe_shortest_path_lengths(self):
        """Calculate the shortest paths from probe cells to every
        other cell.

        Return a dictionary of dictionaries. self.bg_path[v1][v2] ==
        pathlength from vertex with index v1 to that with index v2.
        """
        if hasattr(self, 'probe_paths'):
            return self.probe_path_lengths
        self.probe_vertices = self.ampa_graph.vs.select(name_in=self.probe_targets)
        self.probe_path_lengthss = defaultdict(dict)
        if self._probe_shortest_paths is None:
            self._probe_shortest_paths = {}
            for vv in self.probe_vertices:
                paths = self.ampa_graph.get_all_shortest_paths(vv.index, mode=ig.OUT)
                self._probe_shortest_paths[vv['name']] = paths
                for path in paths:
                    self.probe_path_lengths[vv.index][path[-1]] =  len(path) - 1
        return self.probe_path_lengths

    def calc_stim_shortest_distance_del_p_correlation(self, celltype='', windows=[10e-3, 20e-3, 30e-3, 40e-3, 50e-3], delays=[0.0], overwrite=False):
        """Correlate the shortest distance of a cell from the
        stimulated set. This does not (yet) take synaptic strength
        into account."""
        ret = []
        bgpathlenmap = self.get_bg_shortest_paths()
        probepathlenmap = self.get_probe_shortest_path_lengths()        
        probeshortestmap = dict([(cell, min(pathlen)) for cell, pathlen in probepathlenmap.items()])
        cells, del_p_list, = self.get_stim_del_p(celltype, windows, delays, overwrite)
        vs = [self.ampa_graph.vs.select(name_eq=cell)[0] for cell in cells]
        for (window, delay, del_p) in del_p_list:
            probeshortest = []
            for vc in vs:
                lengths = [probepathlenmap[vp.index][vc.index] for vp in self.probe_vertices]
                probeshortest.append(min(lengths))
            corrcoef = np.corrcoef(probeshortest, del_p, rowvar=False)
            ret.append((window, delay, corrcoef))
        return (cells, ret)

    def calc_distance_del_p_corrceof(self, pathlengthmap, cells, del_p_list):
        ret = []
        for (window, delay, del_p) in del_p_list:
            # We list the vertices in the order of the cells. Also
            # checkin for equality if faster than checking membership.
            vs = [self.ampa_graph.vs.select(name_eq=cell)[0] for cell in cells]
            pathlengths = [pathlengthmap[cell] for cell in cells]
            corrcoef = np.corrcoef(pathlengths, del_p)
            ret.append((window, delay, corrcoef))
        return ret

    def calc_stim_distance_del_p_corrrelation(sellf, celltype='', windows=[10e-3, 20e-3, 30e-3, 40e-3, 50e-3], delays=[0.0], overwrite=False):
        """Correlate the distance to the probe stimulated cells to
        del_p. I measure the distance as resistance in parallel:
        
        1/equivalent = 1/d1 + 1/d2 + 1/d3 + ...

        The situation is intuitively similar to parallel resistors
        where each different path gives an additional route for signal
        to reach the target."""
        probepathlenmap = {}
        for cell, pathlengths in self.__calc_probe_shortest_paths().items():
            probepathlenmap[cell] = 1.0/sum([1.0/length for length in pathlengths])
        
            
    
                                
        
        

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
        pyplot.figure(figsize=(8,11))
        pyplot.clf()
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
            pyplot.subplot(rowcount, 2, plotindex)
            plotindex += 1
            pyplot.bar(np.arange(0,len(deltap), 1.0), deltap)
            pyplot.title('delay:%g width:%g' % (delay, window))
            # pyplot.legend()
        pyplot.suptitle('P(spike/probe) - P(spike/background)\nFile: %s' % (filename))
        figfile = '%s' % (filename.replace('.h5', '.png').replace('stim_prob_', 'stim_delprob_%s' % (celltype)))
        pyplot.savefig(figfile)
        print 'Figure saved in:', figfile        
        dataf.close()
        pyplot.show()
        
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
        pyplot.figure(figsize=(8,11))
        pyplot.clf()
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
            pyplot.subplot(rowcount, 2, plotindex)
            plotindex += 1
            pyplot.bar(np.arange(0,len(deltap), 1.0), deltap)
            pyplot.title('delay:%g width:%g' % (delay, window))
            # pyplot.legend()
        pyplot.suptitle('P(spike/probe) - P(spike/background)\nFile: %s' % (filename))
        figfile = '%s' % (filename.replace('.h5', '.png').replace('stim_prob_', 'stim_delprob_%s' % (celltype)))
        pyplot.savefig(figfile)
        print 'Figure saved in:', figfile        
        dataf.close()
        pyplot.show()
    

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
                figure = pyplot.figure()
                pyplot.title('window: %g, delay: %g' % (window, delay))                
                pyplot.hist([prob_post_bg, prob_post_probe], bins=np.arange(0, 1.1, 0.1), normed=True, histtype='bar', label=['prob-bg', 'prob-probe'])
                pyplot.ylim([0.0, 10.0])
                pyplot.xlim([0.0, 1.1])
                pyplot.legend(prop={'size':'xx-small'})
                # pyplot.show()
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
    do_run_dump_stimulus_linked_probabilities(sys.argv[1])
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
