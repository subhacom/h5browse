# histogram_hhchan_gk.py --- 
# 
# Filename: histogram_hhchan_gk.py
# Description: 
# Author: 
# Maintainer: 
# Created: Thu Jul  4 11:58:19 2013 (+0530)
# Version: 
# Last-Updated: Thu Jul  4 15:43:45 2013 (+0530)
#           By: subha
#     Update #: 97
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

"""Display histogram of HHChannel conductances"""

from itertools import izip
from collections import defaultdict
import h5py as h5
import pylab as pl

fname_list = {
    'network_20120919_172536_12276.h5.new',
    'network_20120922_195344_13808.h5.new',
    'network_20120925_140523_15171.h5.new',
    'network_20120928_095506_16949.h5.new',
    'network_20120929_184651_17981.h5.new',
    'network_20121003_091501_19886.h5.new',
    'network_20121004_201146_20645.h5.new',
    'network_20121006_081815_23857.h5.new',
    'network_20121008_104359_25161.h5.new',
    'network_20121012_140308_27319.h5.new',
    'network_20121014_184919_28619.h5.new',
    'network_20121105_144428_16400.h5.new',
    'network_20121107_100729_29479.h5.new',
    'network_20121108_210758_30357.h5.new',
    'network_20121112_112211_685.h5.new',
    'network_20121114_091030_2716.h5.new',
    'network_20121116_091100_3774.h5.new',
    'network_20121118_132702_5610.h5.new',
    'network_20121120_090612_6590.h5.new',
    'network_20121122_145449_8016.h5.new',
    }

def histogram_all_channels(netfile):
    """Display the Gbar of all channels in `netfile`."""
    channels = pl.char.rpartition(netfile['/network/hhchan']['f0'], '/')[:,-1]
    channames = set(channels)    
    Gbar = netfile['/network/hhchan']['f1'] 
    chan_G_dict = {}
    for ii, chan in enumerate(channames):
        pl.figure(ii+1)
        gbar = Gbar[pl.where(channels == chan)].copy()
        pl.title(chan)
        pl.hist(gbar)
    pl.show()

def get_bad_channels(netfile):
    chan = pl.asarray(netfile['/network/hhchan'])
    bad = chan[pl.where(chan['f1'] < 0)]
    return bad
    
import sys
from util import makepath

if __name__ == '__main__':
    # if len(sys.argv) < 2:
    #     print """Usage: %s netfilename
    #     Display histograms of HHChannel Gbars from file `netfilename`.""" % (sys.argv[0])
    #     sys.exit(-1)
    # netfile = h5.File(sys.argv[1], 'r')
    # histogram_all_channels(netfile)
    for fname in fname_list:
        fpath = makepath(fname, datadir='/data/subha/rsync_ghevar_cortical_data_clone/')
        try:
            fhandle = h5.File(fpath, 'r')
        except:
            print 'Could not open %s' % fpath
            continue
        try:
            bad = get_bad_channels(fhandle)
            if bad.size > 0:
                print '!!!!!! ', fname, '!!!!!!'
                for b in bad:
                    print b 
                print
            else:
                print fname, '.... OK'
        except:
            print 'Error reading channel data from', fname
        finally:
            fhandle.close()
        


# 
# histogram_hhchan_gk.py ends here
