# analyze_excitation_inhibition_balance.py --- 
# 
# Filename: analyze_excitation_inhibition_balance.py
# Description: 
# Author: 
# Maintainer: 
# Created: Wed Nov 14 12:36:04 2012 (+0530)
# Version: 
# Last-Updated: Thu Nov 15 17:40:50 2012 (+0530)
#           By: subha
#     Update #: 166
# URL: 
# Keywords: 
# Compatibility: 
# 
# 

# Commentary: 
# 
# This is for analyzing the excitation inhibition balance
# 
# 

# Change log:
# 
# 
# 
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.
# 
# 

# Code:

import sys
import h5py as h5
import os
import subprocess
from datetime import datetime
from operator import itemgetter
from get_files_by_ts import *
import numpy as np
from matplotlib import pyplot as plt
import random

if __name__ == '__main__':    
    filenames = find_files('/data/subha/rsync_ghevar_cortical_data_clone', '-iname', 'data_*.h5') # Find all data files in the directory
    current_fts = get_fname_timestamps(filenames, '20120918', '20121201') # These simulations were done from 2012-09-19 till 2012-11-??
    # We'll store the file (descriptor, timestamp)  in fdts
    fdts = []
    notes = {}    
    current_fnames = []
    for v in current_fts:
        fd = None
        try:
            fd = h5.File(v[0], 'r')
            fdts.append((fd, v[1]))
            notes[v[0]] = fd.attrs['notes']            
            current_fnames.append(v[0])
        except IOError, e:
            print 'Error accessing file %s: %s' % (v[0], e)
        except KeyError, e1:
            print 'No `notes` attribute in', v[0]
        finally:
            if fd:
                fd.close()
    categories = classify_files_by_cellcount(current_fnames)
    # After categorising the good files, we work with only those files
    # with 240 spiny stellate cells (others test simulations)
    goodfiles = {}
    print '=== printing filenames and notes ==='
    for cc, fnames in categories.items():        
        print '^', cc
        for fname in fnames:
            print '  ', fname
            print '    ', notes[fname]
        if cc.SpinyStellate == 240:
            goodfiles[cc] = fnames
    print '---'
    data = {}
    for cc, fnames in goodfiles.items():        
        data.update(load_spike_data(fnames))
    print 'Loaded data from', len(data), 'files'
    colordict = load_celltype_colors()
    print colordict
    filefiguremap = {}
    figindices = range(1, 1+len(data))
    current_index = 0
    random.shuffle(figindices)
    categories = goodfiles.keys()
    random.shuffle(categories)    
    for cc in categories:
        fnames = list(goodfiles[cc])
        random.shuffle(fnames)
        for fn in fnames:
            fdata = data[fn]
            cells = sorted(fdata.keys())
            filefiguremap[fn] = plt.figure('%d' % (figindices[current_index]))
            # plt.suptitle('DeepBasket: %d, %s' % (cc.DeepBasket, fn))
            deepbasket_count = 0
            count = 1
            for cell in cells:
                celltype = cell.split('_')[0]
                if celltype == 'DeepBasket':
                    deepbasket_count += 1
                    if deepbasket_count > 30:
                        continue                        
                color=colordict[celltype]
                plt.plot(fdata[cell], np.ones(len(fdata[cell]))*count, color=color, ls='', marker='|')
                count += 1
            current_index += 1
    with open('filetofigure_%s.txt' % (datetime.now().strftime('%Y%m%d_%H%M%S')), 'w') as fd:
        for cc, fnames in goodfiles.items():
            for fn in fnames:
                fd.write('%d %s %s\n' % (cc.DeepBasket, fn, filefiguremap[fn].canvas.manager.window.title))
    plt.show()
        
                
# 
# analyze_excitation_inhibition_balance.py ends here
