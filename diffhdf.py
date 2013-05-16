# diffhdf.py --- 
# 
# Filename: diffhdf.py
# Description: 
# Author: 
# Maintainer: 
# Created: Thu May 16 11:51:53 2013 (+0530)
# Version: 
# Last-Updated: Thu May 16 17:06:35 2013 (+0530)
#           By: subha
#     Update #: 105
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

"""Widget to diff two hdf5 files. Particularly for my simulation settings."""
import sys
import os
import subprocess
import numpy as np
import h5py as h5
from PyQt4 import QtCore as qcore
from PyQt4 import QtGui as qgui
from PyQt4 import QtWebKit as wkit
from PyQt4.Qt import Qt

import difflib

def diff_nodes(fromfile, tofile, nodepath):
    """Create a diff of contents under `fromnode` and `tonode`."""
    args = ['h5dump']
    with h5.File(fromfile, 'r') as fromfd:
        nodetype = fromfd[nodepath].attrs['CLASS']
    if nodetype == 'GROUP':
        args.append('-g')
    elif nodetype == 'TABLE':
        args.append('-d')
    else:
        raise Exception('Cannot handle class %s' % (nodetype))
    args.append(nodepath)
    from_proc = subprocess.Popen(args + [fromfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    to_proc = subprocess.Popen(args + [tofile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    from_out, from_err = from_proc.communicate()
    print '*****', from_out
    print '###', from_err
    from_strlist = from_out.split('\n')
    print from_strlist
    to_out, to_err = to_proc.communicate()
    print '*****', to_out
    to_strlist = to_out.split('\n')
    print to_strlist
    differ = difflib.HtmlDiff()
    tab = differ.make_file(from_strlist, to_strlist)
    print tab
    return tab

def view_diff(fromfile, tofile, nodepath):    
    tab = diff_nodes(fromfile, tofile, nodepath)
    view = qgui.QTextBrowser()
    # view = wkit.QWebView()

    view.setText(tab)
    # view.load(qcore.QUrl('http://www.google.com'))
    view.show()
    
fromfile = '/data/subha/rsync_ghevar_cortical_data_clone/2013_05_13/data_20130513_090344_30246.h5'
tofile = '/data/subha/rsync_ghevar_cortical_data_clone/2011_09_26/data_20110926_211607_10136.h5'
if __name__ == '__main__':
    app = qgui.QApplication(sys.argv)
    tab = diff_nodes(fromfile, tofile, '/runconfig')
    view = qgui.QTextBrowser()
    view.setText(tab)
    print 'Here'
    view.show()
    sys.exit(app.exec_())



# 
# diffhdf.py ends here
