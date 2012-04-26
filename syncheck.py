# syncheck.py --- 
# 
# Filename: syncheck.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Apr 25 10:45:32 2012 (+0530)
# Version: 
# Last-Updated: Thu Apr 26 20:10:58 2012 (+0530)
#           By: subha
#     Update #: 175
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
    return min(data) + data/(max(data) - min(data))

def get_presynaptic(syntab, cellname, srctype, syntype):
    """Return a view containing the presynaptic cells of `cellname` of
    type `srctype` with synapses of `syntype`"""
    idx = np.char.startswith(syntab['dest'], cellname) & \
        np.char.startswith(syntab['source'], srctype) & \
        np.char.equal(syntab['type'], syntype)
    return syntab[idx]

def plot_presynaptic(cellname, srctype, syntype, netfile, datafile, tstart, tend):
    presynaptic = get_presynaptic(netfile['/network/synapse'][:], cellname, srctype, syntype)
    precells = [item[0] for item in np.char.split(presynaptic['source'], '/')]
    plotdt = datafile.attrs['plotdt']
    simdt = datafile.attrs['simdt']
    istart = int(tstart/plotdt)
    iend = int(tend/plotdt)
    for ii in range(len(precells)):
        print 'Presynaptic cell:', precells[ii]
        pretype = precells[ii].split('_')[0]
        syndata_path = 'gk_%s_%s_from_%s' % (presynaptic['dest'][ii].replace('/', '_'),
                                             syntype,
                                             pretype)
        try:
            gk = np.asarray(datafile['/synapse/' + syndata_path ])
            gk = normalize(gk)[istart:iend]
            # Shift the normalize plots around 0 so they don't overlap too much with the original
            l2d = plt.plot(np.linspace(tstart, tend, len(gk)), 
                     gk + ii - len(precells)/2, 
                     # color=celltype_color_dict[pretype], 
                     ls='-.',
                     label=syndata_path)
            vm = np.asarray(datafile['/Vm/'+ precells[ii]])
            vm = normalize(vm)[istart:iend]
            plt.plot(np.linspace(tstart, tend, len(vm)), 
                     vm + ii - len(precells)/2, 
                     color = l2d[0].get_color(),
                     # color=celltype_color_dict[pretype],
                     label=precells[ii])
        except KeyError:
            print 'No synaptic Gk for', cellname, '<-', pretype

def test_conn(filename):
    h5f = h5.File(filename, 'r')
    syntab = h5f['network']['synapse'][:]
    src = np.char.split(syntab['source'], '/')
    dest = np.char.split(syntab['dest'], '/')
    src = [item[0] for item in src]
    dest = [item[0] for item in dest]
    error = False
    for ii in range(len(src)):
        if src[ii] == dest[ii]:
            print 'Self connection:', syntab[ii]
            error = True
    if error:
        print 'Self connections found in', filename
    h5f.close()

if __name__ == '__main__':
    dfname = '/data/subha/cortical/py/data/2012_04_24/data_20120424_145719_7507.h5'
    nfname = '/data/subha/cortical/py/data/2012_04_24/network_20120424_145719_7507.h5.new'
    cellname = 'SpinyStellate_21'
    sourcetype = ''#'TCR'
    synapsetype = 'nmda'
    df = h5.File(dfname, 'r')
    nf = h5.File(nfname, 'r')
    plotdt = 1.0
    simdt = 1.0
    simtime = 10.0
    for row in df['runconfig/scheduling'][:]:
        if row[0] == 'simdt':
            simdt = float(row[1])
        elif row[0] == 'plotdt':
            plotdt = float(row[1])
        elif row[0] == 'simtime':
            simtime = float(row[1])
    vm = df['/Vm/'+cellname][:]
    vm = normalize(vm)
    plt.plot(np.linspace(0, simtime, len(vm)), 
             vm, 
             color=celltype_color_dict[cellname.split('_')[0]], 
             ls=':',
             label=cellname)
    tstart = 6.0
    tend = 7.5
    plot_presynaptic(cellname, sourcetype, synapsetype, nf, df, tstart, tend)
    plt.legend(loc='lower left')
    plt.show()

# 
# syncheck.py ends here
